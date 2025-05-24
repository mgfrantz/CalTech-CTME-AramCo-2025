from constants import Models
from litellm import acompletion

# Prompt template for the LLM to generate a data population script from SQLAlchemy ORM code
PROMPT = """
You are an expert Python developer. \
Given the following SQLAlchemy ORM class definition, \
generate a Python file that populates the database with realistic data. \
Keep in mind the model of the data; dimensions (tables such as customers, products, etc.) should be realistic, \
and have 1:many relationships to data in fact tables (tables such as orders, invoices, etc.). \
The script should begin with ```python and end with ```.
It should also end with a populate(engine) function that populates the database with the data given an engine.
It should also import the sqlalchemy models from the followig file: {schema_py_file}

SQLAlchemy ORM code:
{orm_code}
"""


def parse_python_code(code: str) -> str:
    """
    Extracts the Python code block from a markdown-formatted string.
    Args:
        code (str): The string containing the code block, possibly with markdown formatting.
    Returns:
        str: The extracted Python code without markdown formatting.
    """
    if "```python" in code:
        code = code.split("```python")[1].split("```", 1)[0]
    elif "```" in code:
        code = code.split("```", 1)[1].split("```", 1)[0]
    return code


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


def write_script_to_file(script: str, output_file: str) -> None:
    """
    Writes a string to a specified output file.
    Args:
        script (str): The script or code to write.
        output_file (str): Path to the output file.
    """
    with open(output_file, "w") as f:
        f.write(script)


async def call_llm(orm_code: str, schema_py_file: str) -> str:
    """
    Calls the LLM to generate a data population script based on the provided ORM code.
    Args:
        orm_code (str): The SQLAlchemy ORM code as a string.
        schema_py_file (str): Path to the schema .py file.
    Returns:
        str: The LLM's response containing the generated script (possibly with markdown formatting).
    """
    response = await acompletion(
        model=Models.GEMINI_MODEL,
        messages=[{"role": "user", "content": PROMPT.format(orm_code=orm_code, schema_py_file=schema_py_file)}],
    )
    return response.choices[0].message.content


async def populate_data(schema_py_file: str, output_file: str) -> None:
    """
    Reads a SQLAlchemy schema file, uses an LLM to generate a data population script, and writes the script to an output file.
    Args:
        schema_py_file (str): Path to the input schema .py file.
        output_file (str): Path to the output .py file where the generated script will be saved.
    """
    # Read the ORM schema code from file
    orm_code = read_schema_py_file(schema_py_file)
    # Generate the data population script using the LLM
    code = await call_llm(orm_code, schema_py_file)
    # Extract the Python code from the LLM's markdown response
    code = parse_python_code(code)
    # Write the generated script to the output file
    write_script_to_file(code, output_file)
