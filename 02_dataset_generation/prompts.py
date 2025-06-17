from langchain.prompts import PromptTemplate
from textwrap import dedent

database_requests_prompt = PromptTemplate(
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

request_to_sqlalchemy_prompt = PromptTemplate(
    template=dedent("""\
You are an expert Python developer. \
You create comprehensive and accurate database models based on customer requests. \
You make sure that column names are clear, and that types are specific. \
You make sure that relations among tables are clear by column naming. \
A customer has requested the creation of a SQLite database with specific tables. \
Please generate SQLAlchemy ORM class definitions for a SQLite database. \
Use declarative_base. Only output valid Python code. \
The python code should begin with ```python and end with ```. 

Database request:
{database_request}
"""),
    input_variables=["database_request"],
)

populate_database_prompt = PromptTemplate(
    template=dedent("""\
You are an expert Python developer. \
Given the following SQLAlchemy ORM class definition, \
generate a Python file that populates the database with realistic data. \
Keep in mind the model of the data; dimensions (tables such as customers, products, etc.) should be realistic, \
and have 1:many relationships to data in fact tables (tables such as orders, invoices, etc.). \
The script should begin with ```python and end with ```. \
The script should use argparse to take a --output or -o argument to specify the output file with a default of "output.db". \
It should also take an --input or -i argument to spefify the .py file containing the sqlalchemy models for imports. \
Based on these parameters, the script should import the models, populate the database with realistic data, and save the database to the output file. \
Use libraries like `faker` and `names` to generate realistic data in appropriate cases. \
Or, feel free to be verbose in the data generation to create a more realistic dataset if `faker` or `names` are not sufficient. \
The SQLAlchemy models are given as a reference below so it's clear what the script should import.

Example usage:
python populate_database.py --input db_model.py --output output.db

SQLAlchemy ORM code:
{orm_code}
"""),
    input_variables=["orm_code"],
)

generate_questions_prompt = PromptTemplate(
    template=dedent("""\
You are an expert data analyst. \
Given the following SQLAlchemy ORM schema, \
generate 15-20 interesting and realistic questions that could be asked about the data, \
and for each, provide the SQL query that would answer it. \
The questions should be balanced between transactional (such as "who had the most bookings over the past week") \
and analytical questions (give me the 3-day rolling average of bookings per day over the past 30 days).

SQLAlchemy ORM code:
{orm_code}
"""),
    input_variables=["orm_code"],
)

class Prompts:
    DATABASE_REQUESTS = database_requests_prompt
    REQUEST_TO_SQLALCHEMY = request_to_sqlalchemy_prompt
    POPULATE_DATABASE = populate_database_prompt
    GENERATE_QUESTIONS = generate_questions_prompt
