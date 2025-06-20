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

IMPORTANT REQUIREMENTS:
1. Use declarative_base from sqlalchemy.orm, NOT from sqlalchemy.ext.declarative (deprecated)
2. Do NOT use the 'type_' parameter in Column definitions - use Enum directly if needed
3. Use proper SQLAlchemy 2.0+ syntax with modern imports
4. Only use standard Column types: Integer, String, Float, DateTime, Boolean, Text
5. NEVER use Enum classes directly in Column() - always use String for enum-like fields
6. Always include proper foreign key relationships with ForeignKey()
7. Use relationship() with back_populates for bidirectional relationships
8. Include create_engine and Base.metadata.create_all() at the end
9. Only output valid Python code that will execute without errors

CORRECT IMPORTS:
```python
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey, create_engine
from sqlalchemy.orm import declarative_base, relationship
```

AVOID:
- sqlalchemy.ext.declarative.declarative_base (deprecated)
- type_ parameter in Column definitions
- Using Enum classes directly in Column() definitions
- Complex custom types that SQLite doesn't support
- Any Column type other than Integer, String, Float, DateTime, Boolean, Text

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

CORE REQUIREMENTS:
1. The script should begin with ```python and end with ```.
2. Use argparse for --output/-o (default: "output.db") and --input/-i (required)
3. Import models dynamically with importlib.util
4. Generate realistic data amounts (20-50 for main tables, 100+ for transaction tables)
5. Data generation: Use faker when convenient, otherwise hardcode realistic values
6. Handle foreign key relationships properly (create parents before children)
7. Use basic try/except error handling
8. Close database connections properly

FLEXIBLE DATA GENERATION:
- Use faker for names, emails, addresses, dates when it makes sense
- For specific business data (product types, statuses, categories), use explicit lists
- For numeric ranges, use reasonable hardcoded values or simple random.randint()
- Don't overcomplicate - working data is better than perfect data

BASIC PATTERN:
```python
import argparse
import importlib.util
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker  # IMPORTANT: sessionmaker is in sqlalchemy.orm
from faker import Faker
import random
from datetime import datetime, timedelta

def main():
    engine = None
    session = None
    try:
        # Import models from the input file  
        spec = importlib.util.spec_from_file_location("models", args.input)
        models = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(models)
        
        # Test that we can access the Base class
        if not hasattr(models, 'Base'):
            raise ImportError("Models file must define 'Base' class")
        
        # Create engine and session
        engine = create_engine(f'sqlite:///{{args.output}}')
        models.Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Generate data - example pattern for proper data insertion
        print("Starting data generation...")
        
        # Create dimension table records first
        customers = []
        for i in range(30):
            customer = models.Customer(name=fake.name(), email=fake.email())
            customers.append(customer)
        
        print(f"Creating {{len(customers)}} customer records...")
        session.add_all(customers)
        session.flush()  # CRITICAL: Get IDs before creating dependent records
        print(f"Customer IDs obtained: {{[c.id for c in customers[:3]]}}...")  # Show first 3 IDs
        
        # Create fact table records using foreign keys
        orders = []
        for customer in customers:
            for _ in range(random.randint(1, 5)):
                order = models.Order(
                    customer_id=customer.id,
                    total=fake.pydecimal(left_digits=3, right_digits=2, positive=True)
                )
                orders.append(order)
        
        print(f"Creating {{len(orders)}} order records...")
        session.add_all(orders)
        
        # Validate data before committing
        customer_count = session.query(models.Customer).count()
        order_count = session.query(models.Order).count()
        print(f"Pre-commit validation: {{customer_count}} customers, {{order_count}} orders")
        
        if customer_count == 0 or order_count == 0:
            raise ValueError("No data was generated - check model relationships")
            
        session.commit()
        print("Data generation completed successfully!")
        
    except Exception as err:
        print(f"Error importing models or generating data: {{err}}")
        if session is not None:
            try:
                session.rollback()
            except:
                pass
    finally:
        if session is not None:
            try:
                session.close()
            except:
                pass
        if engine is not None:
            try:
                engine.dispose()
            except:
                pass

if __name__ == "__main__":
    main()
```

SIMPLE GUIDELINES:
- Let SQLAlchemy handle primary key auto-increment
- For unique fields like emails, use sets to track used values if needed
- For DateTime fields, use fake.date_time_between() or fake.date_between()
- Create parent records first, flush to get IDs, then create children
- Don't overthink constraints - focus on generating working test data

SQLAlchemy ORM code:
{orm_code}
"""),
    input_variables=["orm_code"],
)

generate_questions_prompt = PromptTemplate(
    template=dedent("""\
You are an expert data analyst. \
Given the following SQLAlchemy ORM schema, \
generate exactly 15-20 interesting and realistic questions that could be asked about the data, \
and for each, provide the SQL query that would answer it. \

IMPORTANT REQUIREMENTS:
1. Generate EXACTLY 15-20 questions (never return an empty list)
2. Use only standard SQLite-compatible SQL syntax
3. Avoid PostgreSQL-specific functions like INTERVAL - use date arithmetic instead
4. Use SQLite date functions: date(), datetime(), julianday() for date calculations
5. For "recent month" use: WHERE date_column >= date((SELECT MAX(date_column) FROM table_name), '-1 month')
6. For "past 30 days" use: WHERE date_column >= date((SELECT MAX(date_column) FROM table_name), '-30 days')
7. For rolling averages, use window functions or subqueries
8. Use MAX(date_column) to find the most recent date in synthetic data
9. Each question should test different aspects of the schema
10. Mix simple queries (counts, sums) with complex analytical queries

QUESTION TYPES TO INCLUDE:
- Count/aggregation queries (How many X are there?)
- Top N queries (Who are the top 5 customers by orders?)
- Time-based analysis (What's the trend over time?)
- Relationship queries (Which X has the most Y?)
- Average/statistical queries (What's the average X?)

SQLITE DATE EXAMPLES:
- Recent month: date_column >= date((SELECT MAX(date_column) FROM table_name), '-1 month')
- Past week: date_column >= date((SELECT MAX(date_column) FROM table_name), '-7 days')
- Past 30 days: date_column >= date((SELECT MAX(date_column) FROM table_name), '-30 days')
- Date arithmetic: julianday(date2) - julianday(date1) as days_diff

The questions should be balanced between transactional (such as "who had the most bookings in the most recent month") \
and analytical questions (give me the 3-day rolling average of bookings per day over the past 30 days) that would make insightful plots. \
Since the data is synthetic, we shouldn't expect it to be recent, so make sure to use expressions like MAX(date) to assume the most recent date.

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
