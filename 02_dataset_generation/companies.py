import json
from typing import List

from litellm import completion
from pydantic import BaseModel, Field

from ctme.utils import get_root_dotenv

from .constants import Models

_ = get_root_dotenv()


class CompanyDatabaseDescriptions(BaseModel):
    descriptions: List[str] = Field(
        ..., description="A list of descriptions of companies and their databases"
    )


prompt = """\
Please help create requests for database schemas for companies.
Examples: 
I'd like a database schema for an ecommerce company selling electronics. It should manage customers, orders, and inventory.
I'd like a database schema for a customer support system. It should track customers, tickets, agents, and responses.

Please return a list of {num_requests} requests for database schemas for companies. \
Each request should be 3-5 tables that represent the company's business. \
Make sure to follow the requested JSON schema.
"""


def generate_company_database_descriptions(
    num_requests: int = 20, output_file: str | None = "db_requests.json"
) -> List[str]:
    response = completion(
        model=Models.OPENROUTER_MODEL,
        messages=[
            {"role": "user", "content": prompt.format(num_requests=num_requests)}
        ],
        response_format=CompanyDatabaseDescriptions,
    )
    descriptions: list[str] = CompanyDatabaseDescriptions.model_validate_json(
        response.choices[0].message.content
    ).descriptions

    if output_file is not None:
        with open(output_file, "w") as f:
            json.dump(descriptions, f)

    return descriptions


if __name__ == "__main__":
    descriptions = generate_company_database_descriptions()
    print(descriptions)
