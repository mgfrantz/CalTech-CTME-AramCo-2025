"""
Module for generating company database schema descriptions using LLM.

This module provides functionality to generate realistic database schema requests
for various types of companies using OpenAI's language models. It creates prompts
that ask for database schemas representing different business domains and saves
the generated descriptions to a JSON file.
"""

import json
import os
from textwrap import dedent
from typing import List

# Import custom constants for model configurations
from constants import Models
# LangChain imports for prompt templating and OpenAI integration
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
# Pydantic for data validation and structured output
from pydantic import BaseModel, Field

# Custom utility for loading environment variables
from ctme.utils import get_root_dotenv

# Load environment variables from root .env file
_ = get_root_dotenv()


class CompanyDatabaseDescriptions(BaseModel):
    """
    Pydantic model for structured output from the LLM.
    
    This model ensures that the LLM returns a properly formatted response
    containing a list of company database schema descriptions.
    """
    descriptions: List[str] = Field(
        ..., description="A list of descriptions of companies and their databases"
    )


# Create a prompt template for generating database schema requests
prompt = PromptTemplate(
    template=dedent("""\
    Please help create requests for database schemas for companies.
    Examples: 
    I'd like a database schema for an ecommerce company selling electronics. It should manage customers, orders, and inventory.
    I'd like a database schema for a customer support system. It should track customers, tickets, agents, and responses.

    Please return a list of {num_requests} requests for database schemas for companies. \
    Each request should be 3-5 tables that represent the company's business. \
    Make sure to follow the requested JSON schema.
    """),
    input_variables=["num_requests"],
)

# Initialize the OpenAI chat model with configuration from environment variables
# Uses OpenRouter as a proxy to access various LLM models
llm = ChatOpenAI(
    model=Models.OPENROUTER_MODEL,  # Model specified in constants
    api_key=os.environ["OPENROUTER_API_KEY"],  # API key from environment
    base_url=os.environ["OPENROUTER_API_URL"],  # Base URL for OpenRouter API
).with_structured_output(CompanyDatabaseDescriptions)  # Enforce structured output using Pydantic model

# Create a chain that combines the prompt template with the LLM
# This allows for easy invocation with input parameters
llm_chain = prompt | llm

def generate_company_database_descriptions(
    num_requests: int = 20, output_file: str | None = "db_requests.json"
) -> List[str]:
    """
    Generate company database schema descriptions using the LLM chain.
    
    This function invokes the LLM to generate a specified number of database
    schema requests for different types of companies. Each request describes
    a business scenario and the database tables needed to support it.
    
    Args:
        num_requests (int): Number of database schema descriptions to generate.
                           Defaults to 20.
        output_file (str | None): Path to save the generated descriptions as JSON.
                                 If None, no file is saved. Defaults to "db_requests.json".
    
    Returns:
        List[str]: List of generated company database schema descriptions.
    
    Raises:
        Exception: If the LLM API call fails or returns invalid data.
    """
    # Invoke the LLM chain with the specified number of requests
    response = llm_chain.invoke({"num_requests": num_requests})
    descriptions: list[str] = response.descriptions

    # Save the generated descriptions to a JSON file if output_file is specified
    if output_file is not None:
        with open(output_file, "w") as f:
            json.dump(descriptions, f)

    return descriptions


# Main execution block - runs when the script is executed directly
if __name__ == "__main__":
    # Generate company database descriptions using default parameters
    descriptions = generate_company_database_descriptions()
    # Print the generated descriptions to console for review
    print(descriptions)
