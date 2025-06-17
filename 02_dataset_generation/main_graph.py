import asyncio
import operator
import os
from typing import Annotated, List

from constants import Models
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph
from langgraph.types import Send
from models import CompanyDatabaseDescriptions
from prompts import Prompts
from db_graph import graph as db_graph
from db_graph import DatabaseState
from typing_extensions import TypedDict

from ctme.utils import get_root_dotenv

_ = get_root_dotenv()

# Define LLMs
base_llm = ChatOpenAI(
    model=Models.LLAMA3_3_70B,  # Model specified in constants
    api_key=os.environ["OPENROUTER_API_KEY"],  # API key from environment
    base_url=os.environ["OPENROUTER_API_URL"],  # Base URL for OpenRouter API
)

company_descriptions_llm = base_llm.with_structured_output(
    CompanyDatabaseDescriptions
)  # LLM with structured output


# Define the graph state
class State(TypedDict):
    company_descriptions: List[str]  # company descriptions
    databases: Annotated[List[dict], operator.add]  # database schemas
    num_requests: int = 2


# Define the nodes.
# First, we need a node to generate company descriptions.
generate_company_chain = Prompts.DATABASE_REQUESTS | company_descriptions_llm


async def generate_company_descriptions(state: State) -> State:
    """
    Generate company descriptions.
    """
    company_descriptions: CompanyDatabaseDescriptions = (
        await generate_company_chain.ainvoke({"num_requests": state.get("num_requests", 2)})
    )
    descriptions = company_descriptions.descriptions
    return {"company_descriptions": descriptions}

def add_database_to_state(state: DatabaseState) -> State:
    return {"databases": [state]}


# Next, we need a node to map the db schema generation over the compnay descriptions.
def map_db_schema_over_company_descriptions(state: State) -> State:
    """
    Map the db schema generation over the company descriptions.
    """
    return [
        Send("create_database", {"database_request": request})
        for request in state["company_descriptions"]
    ]


# Create the graph
builder = StateGraph(State)

builder.add_node("generate_company_descriptions", generate_company_descriptions)
builder.add_node("create_database", db_graph)
builder.add_node("add_database_to_state", add_database_to_state)
builder.add_conditional_edges(
    "generate_company_descriptions",
    map_db_schema_over_company_descriptions,
    ["create_database"],
)
builder.add_edge(START, "generate_company_descriptions")
builder.add_edge("create_database", "add_database_to_state")
builder.add_edge("add_database_to_state", END)

graph = builder.compile()


async def main():
    result = await graph.ainvoke({"num_requests": 1})
    for i, database in enumerate(result["databases"]):
        print(f"Database {i}:")
        print(database)
        print("\n\n")

if __name__ == "__main__":
    asyncio.run(main())