import asyncio
import os
import structlog

from .constants import Models
from langchain_core.messages import AIMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph
from .prompts import Prompts
from typing import List
from typing_extensions import TypedDict
from .models import QuestionSqlPairs

from ctme.utils import get_root_dotenv

logger = structlog.get_logger(__name__)

_ = get_root_dotenv()


# General utilities
def parse_python_code(code: str) -> str:
    """
    Parse the python code from the response with robust error handling.
    """
    # Handle different code block formats
    if "```python" in code:
        extracted = code.split("```python")[1].split("```")[0]
        return extracted.strip()
    elif "```" in code:
        # Try generic code blocks
        parts = code.split("```")
        if len(parts) >= 3:
            # Skip the first part (before first ```) and take the second part (the code)
            extracted = parts[1].strip()
            if extracted:
                return extracted
    
    # If no code blocks found, log error and try to extract code patterns
    logger.error("No python code blocks found in response", 
                response=code[:500],  # Show more context
                full_response_length=len(code))
    
    # Enhanced code pattern detection
    lines = code.split('\n')
    code_lines = []
    found_code = False
    
    # Look for common Python patterns
    python_indicators = [
        'import ', 'from ', 'def ', 'class ', 'engine = ', 'Base = ',
        'Column(', '@', 'if __name__', 'sqlalchemy', 'create_engine',
        'session.', 'models.', 'fake.', 'parser.add_argument'
    ]
    
    for line in lines:
        stripped_line = line.strip()
        if any(indicator in line for indicator in python_indicators):
            found_code = True
        if found_code and stripped_line:
            code_lines.append(line)
    
    if code_lines:
        extracted_code = '\n'.join(code_lines)
        logger.info("Extracted code using pattern matching", 
                   extracted_lines=len(code_lines))
        return extracted_code
    else:
        # Emergency fallback - return sanitized response
        logger.warning("Could not extract valid Python code, returning sanitized response")
        # Remove markdown and try to clean up
        cleaned = code.replace('```', '').strip()
        return cleaned if cleaned else "# No valid code could be extracted"


def extract_content(ai_message: AIMessage) -> str:
    """
    Extract the content string from an AIMessage object.
    """
    return ai_message.content


# Define LLMs
base_llm = ChatOpenAI(
    model=Models.QWEN2_5_72B,  # Use non-free version for higher rate limits
    api_key=os.environ["OPENROUTER_API_KEY"],  # API key from environment
    base_url=os.environ["OPENROUTER_API_URL"],  # Base URL for OpenRouter API
    temperature=0.1,  # Lower temperature for more consistent code generation
    max_retries=3,
    request_timeout=120,
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
    logger.info("Creating database models", 
                database_request=state["database_request"][:100] + "..." if len(state["database_request"]) > 100 else state["database_request"])
    
    db_model = await generate_db_model_chain.ainvoke(
        input={
            "database_request": state["database_request"],
        }
    )
    
    logger.info("Database models created")
    return {"database_models": db_model}


async def populate_database(state: DatabaseState) -> DatabaseState:
    """
    Populate the database with data.
    """
    logger.info("Generating database population script")
    
    # We need to write out the python files we want to reference and execute.
    database_population_code = await populate_database_chain.ainvoke(
        input={
            "orm_code": state["database_models"],
        }
    )
    
    logger.info("Database population script generated")
    return {"populate_database_script": database_population_code}


async def generate_questions(state: DatabaseState) -> DatabaseState:
    """
    Generate questions about the database.
    """
    logger.info("Generating questions and SQL pairs")
    
    questions = await generate_questions_chain.ainvoke(
        input={"orm_code": state["database_models"]}
    )
    
    logger.info("Questions and SQL pairs generated", 
                question_count=len(questions.questions))
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