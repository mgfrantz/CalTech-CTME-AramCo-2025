import asyncio
import json
from typing import List, Dict, Any
from tenacity import retry, stop_after_attempt, wait_fixed

from litellm import acompletion
from constants import Models

PROMPT_TEMPLATE = """
You are an expert Python developer. \
Given the following list of tables (with columns and types), \
generate SQLAlchemy ORM class definitions for a SQLite database.\
Use declarative_base. Only output valid Python code. \
The code should end with a create() function that creates the in-memory sqlite database. \
The python code should begin with ```python and end with ```.

Tables:
{tables_json}
"""

def parse_python_code(code: str) -> str:
    """
    Parse the python code from the response.
    """
    return code.split('```python')[1].split('```')[0]

def build_prompt(tables: List[Dict[str, Any]]) -> str:
    """
    Build the LLM prompt for generating SQLAlchemy ORM code from table definitions.
    """
    return PROMPT_TEMPLATE.format(tables_json=json.dumps(tables, indent=4))

@retry(stop=stop_after_attempt(4), wait=wait_fixed(15))
async def tables_to_sqlalchemy_file(
    tables: List[Dict[str, Any]],
    output_file: str = "output_sqlalchemy_schema.py",
    semaphore: asyncio.Semaphore = None,
) -> None:
    """
    Given a list of table definitions, generate a SQLAlchemy ORM schema for SQLite and write it to a .py file.
    Uses an LLM to generate the code.

    Args:
        tables: List of table definitions (dicts with 'table_name' and 'columns').
        output_file: Path to the output .py file.
    """
    prompt = build_prompt(tables)
    response = await acompletion(
        model=Models.GEMINI_MODEL,
        messages=[{"role": "user", "content": prompt}],
    )
    code = response.choices[0].message.content
    code = parse_python_code(code)
    with open(output_file, "w") as f:
        f.write(code)