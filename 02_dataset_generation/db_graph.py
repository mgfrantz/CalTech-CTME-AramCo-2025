import asyncio
import os

from constants import Models
from langchain_core.messages import AIMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph
from prompts import Prompts
from typing import List
from typing_extensions import TypedDict
from models import QuestionSqlPairs

from ctme.utils import get_root_dotenv

_ = get_root_dotenv()


# General utilities
def parse_python_code(code: str) -> str:
    """
    Parse the python code from the response.
    """
    return code.split("```python")[1].split("```")[0]


def extract_content(ai_message: AIMessage) -> str:
    """
    Extract the content string from an AIMessage object.
    """
    return ai_message.content


# Define LLMs
base_llm = ChatOpenAI(
    model=Models.LLAMA3_3_70B,  # Model specified in constants
    api_key=os.environ["OPENROUTER_API_KEY"],  # API key from environment
    base_url=os.environ["OPENROUTER_API_URL"],  # Base URL for OpenRouter API
)

question_sql_pairs_llm = base_llm.with_structured_output(QuestionSqlPairs)


class DatabaseState(TypedDict):
    database_request: str  # the original request for the database
    database_models: (
        str  # this is a python file containing the sqlalchemy models for the database
    )
    populate_database_script: (
        str  # this is a python script to create and populate a database
    )
    question_sql_pairs: List[dict]

    def __repr__(self) -> str:
        return f"DatabaseState(database_request={self['database_request'][:300]}..., database_models={self['database_models'][:300]}..., populate_database_script={self['populate_database_script'][:300]}..., question_sql_pairs={self['question_sql_pairs'][:300]}...)"
    
    def __str__(self) -> str:
        return self.__repr__()


# Next, we need a node to generate database schemas, populate the databases, and populate the questions and answers.
generate_db_model_chain = (
    Prompts.REQUEST_TO_SQLALCHEMY | base_llm | StrOutputParser() | parse_python_code
)
populate_database_chain = (
    Prompts.POPULATE_DATABASE | base_llm | StrOutputParser() | parse_python_code
)
generate_questions_chain = (
    Prompts.GENERATE_QUESTIONS | question_sql_pairs_llm
)


async def create_database_models(state: DatabaseState) -> DatabaseState:
    """
    Generate a database schema.
    """
    db_model = await generate_db_model_chain.ainvoke(
        input={
            "database_request": state["database_request"],
        }
    )
    return {"database_models": db_model}


async def populate_database(state: DatabaseState) -> DatabaseState:
    """
    Populate the database with data.
    """
    # We need to write out the python files we want to reference and execute.
    database_population_code = await populate_database_chain.ainvoke(
        input={
            "orm_code": state["database_models"],
        }
    )
    return {"populate_database_script": database_population_code}


async def generate_questions(state: DatabaseState) -> DatabaseState:
    """
    Generate questions about the database.
    """
    questions = await generate_questions_chain.ainvoke(
        input={"orm_code": state["database_models"]}
    )
    return {"question_sql_pairs": questions.model_dump()}



builder = StateGraph(DatabaseState)
# Add nodes
builder.add_node("create_database_models", create_database_models)
builder.add_node("populate_database", populate_database)
builder.add_node("generate_questions", generate_questions)
# Add edges
builder.add_edge(START, "create_database_models")
builder.add_edge("create_database_models", "populate_database")
builder.add_edge("populate_database", "generate_questions")
builder.add_edge("generate_questions", END)

graph = builder.compile()

if __name__ == "__main__":
    output = asyncio.run(
        graph.ainvoke(
            {
                "database_request": "A database with a customers table, an orders table, and a products table."
            }
        )
    )
    db_schema = output["database_models"]
    db_population_script = output["populate_database_script"]
    print("Database schema:")
    print(db_schema)
    print("\n\nDatabase population script:")
    print(db_population_script)
    print("\n\nQuestions:")
    print(output["question_sql_pairs"])