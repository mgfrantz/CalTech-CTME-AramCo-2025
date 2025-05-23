import argparse
import asyncio
import json
from typing import List

import pandas as pd
from litellm import acompletion
from pydantic import BaseModel
from rich import print
from tenacity import retry, stop_after_attempt, wait_fixed

from .constants import Models


class Column(BaseModel):
    "A column for a table in a sqlite database"

    column_name: str
    column_type: str


class Table(BaseModel):
    "A table in a sqlite database"

    table_name: str
    columns: List[Column]


class DatabaseSchema(BaseModel):
    "A schema for a SQLite Database"

    tables: List[Table]


class DatabaseSchemaWithRequest(DatabaseSchema):
    "A schema for a SQLite Database with the original request"

    request: str

    @classmethod
    def from_database_schema(cls, database_schema: DatabaseSchema, request: str):
        return cls(
            request=request,
            tables=database_schema.tables,
        )


system_prompt = """You are an expert database architect who specializes in SQLite. \
You create comprehensive and accurate database designs based on customer requests. \
You make sure that column names are clear, and that types are specific. \
You make sure that relations among tables are clear by column naming. \
You always follow the expected json output.

Please create a list of database schemas based on the following request:
{request}
"""


@retry(stop=stop_after_attempt(4), wait=wait_fixed(15))
async def generate_schemas(request, semaphore):
    """Generate database schemas with concurrency limited by a semaphore."""
    async with semaphore:
        response = await acompletion(
            model=Models.GEMINI_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": system_prompt.format(request=request),
                }
            ],
            response_format=DatabaseSchema,
        )
        return DatabaseSchema.model_validate_json(response.choices[0].message.content)


async def generate_schemas_batch(requests: List[str], concurrency: int = 3):
    """Generate schemas for a batch of requests, limiting concurrency to the specified value."""
    semaphore = asyncio.Semaphore(concurrency)
    tasks = [generate_schemas(request, semaphore) for request in requests]
    return await asyncio.gather(*tasks)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("input_file", type=str, default="db_requests.json")
    parser.add_argument("output_file", type=str, default="db_schemas.json")
    parser.add_argument("--hf_repo", type=str, default=None)
    parser.add_argument("--concurrency", type=int, default=2, help="Maximum number of concurrent schema generations.")
    return parser.parse_args()


async def main():
    args = parse_args()
    with open(args.input_file, "r") as f:
        requests = json.load(f)
        print(requests)
    schemas = await generate_schemas_batch(requests, concurrency=args.concurrency)
    print(schemas)
    schemas_with_request = [
        DatabaseSchemaWithRequest.from_database_schema(schema, request).model_dump()
        for schema, request in zip(schemas, requests)
    ]
    print(schemas_with_request)
    with open(args.output_file, "w") as f:
        json.dump(schemas_with_request, f, indent=4)


if __name__ == "__main__":
    asyncio.run(main())
