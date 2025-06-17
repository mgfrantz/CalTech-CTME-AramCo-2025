from pydantic import BaseModel, Field
from typing import List

class CompanyDatabaseDescriptions(BaseModel):
    """
    Pydantic model for structured output from the LLM.

    This model ensures that the LLM returns a properly formatted response
    containing a list of company database schema descriptions.
    """

    descriptions: List[str] = Field(
        ..., description="A list of descriptions of companies and their databases"
    )

# Pydantic model for question/SQL pairs
class QuestionSqlPair(BaseModel):
    question: str = Field(..., description="The question to be answered")
    sql: str = Field(..., description="The SQL query that would answer the question")

class QuestionSqlPairs(BaseModel):
    questions: List[QuestionSqlPair] = Field(..., description="The list of question/SQL pairs")