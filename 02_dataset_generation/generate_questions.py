from pydantic import BaseModel, Field
from constants import Models
from litellm import acompletion
from typing import List
import json

# Pydantic model for question/SQL pairs
class QuestionSqlPair(BaseModel):
    question: str = Field(..., description="The question to be answered")
    sql: str = Field(..., description="The SQL query that would answer the question")

class QuestionSqlPairs(BaseModel):
    questions: List[QuestionSqlPair] = Field(..., description="The list of question/SQL pairs")

# Prompt template for the LLM
generate_questions_prompt = """
You are an expert data analyst. \
Given the following SQLAlchemy ORM schema, \
generate 15-20 interesting and realistic questions that could be asked about the data, \
and for each, provide the SQL query that would answer it. \
The questions should be balanced between transactional (such as "who had the most bookings over the past week") \
and analytical questions (give me the 3-day rolling average of bookings per day over the past 30 days). \

SQLAlchemy ORM code:
{orm_code}
"""


def read_schema_py_file(schema_py_file: str) -> str:
    """
    Reads the contents of a Python file containing SQLAlchemy ORM definitions.
    Args:
        schema_py_file (str): Path to the schema .py file.
    Returns:
        str: The contents of the file as a string.
    """
    with open(schema_py_file, "r") as f:
        return f.read()


async def call_llm(orm_code: str) -> str:
    """
    Calls the LLM to generate questions and SQL queries based on the provided ORM code.
    Args:
        orm_code (str): The SQLAlchemy ORM code as a string.
    Returns:
        str: The LLM's response containing the generated JSON list.
    """
    response = await acompletion(
        model=Models.GEMINI_MODEL,
        messages=[{"role": "user", "content": generate_questions_prompt.format(orm_code=orm_code)}],
        response_format=QuestionSqlPairs
    )
    return response.choices[0].message.content


async def generate_questions(schema_py_file: str) -> QuestionSqlPairs:
    """
    Reads a SQLAlchemy schema file, uses an LLM to generate questions and SQL queries, validates them, and writes to a JSON file.
    Args:
        schema_py_file (str): Path to the input schema .py file.

    Returns:
        QuestionSqlPairs: The list of question/SQL pairs.
    """
    # Read the ORM schema code from file
    orm_code = read_schema_py_file(schema_py_file)
    
    response = await call_llm(orm_code)
    return QuestionSqlPairs.model_validate_json(response)