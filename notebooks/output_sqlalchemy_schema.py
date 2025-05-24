
from sqlalchemy import create_engine, Column, Integer, String, REAL, BOOLEAN, DATETIME, DATE
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import func

Base = declarative_base()

class MenuItems(Base):
    __tablename__ = 'MenuItems'

    menu_item_id = Column(Integer, primary_key=True)
    item_name = Column(String, nullable=False)
    description = Column(String)
    category = Column(String)
    price = Column(REAL, nullable=False)
    is_available = Column(BOOLEAN, default=True)

class Orders(Base):
    __tablename__ = 'Orders'

    order_id = Column(Integer, primary_key=True)
    customer_id = Column(Integer)
    staff_id = Column(Integer)
    order_date = Column(DATETIME, default=func.now())
    total_amount = Column(REAL)
    payment_method = Column(String)
    order_status = Column(String)

class OrderItems(Base):
    __tablename__ = 'OrderItems'

    order_item_id = Column(Integer, primary_key=True)
    order_id = Column(Integer)
    menu_item_id = Column(Integer)
    quantity = Column(Integer, nullable=False)
    item_price = Column(REAL)

class Staff(Base):
    __tablename__ = 'Staff'

    staff_id = Column(Integer, primary_key=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    position = Column(String)
    hire_date = Column(DATE)
    salary = Column(REAL)

class Customers(Base):
    __tablename__ = 'Customers'

    customer_id = Column(Integer, primary_key=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    phone_number = Column(String)
    email = Column(String)

def create():
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    return engine

if __name__ == '__main__':
    engine = create()
    Session = sessionmaker(bind=engine)
    session = Session()
