
import datetime
import random
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from output_sqlalchemy_schema import Base, MenuItems, Orders, OrderItems, Staff, Customers


def populate(engine):
    """Populates the database with realistic data."""
    Session = sessionmaker(bind=engine)
    session = Session()

    # Sample Menu Items
    menu_items = [
        MenuItems(item_name="Margherita Pizza", description="Classic tomato, mozzarella, and basil pizza.", category="Pizza", price=12.99, is_available=True),
        MenuItems(item_name="Pepperoni Pizza", description="Pizza with pepperoni slices.", category="Pizza", price=14.99, is_available=True),
        MenuItems(item_name="Vegetarian Pizza", description="Pizza with assorted vegetables.", category="Pizza", price=13.99, is_available=True),
        MenuItems(item_name="Chicken Caesar Salad", description="Romaine lettuce, grilled chicken, parmesan, croutons, and Caesar dressing.", category="Salads", price=9.99, is_available=True),
        MenuItems(item_name="Greek Salad", description="Tomatoes, cucumbers, onions, olives, and feta cheese.", category="Salads", price=8.99, is_available=True),
        MenuItems(item_name="Cheeseburger", description="Beef patty, cheese, lettuce, tomato, and onion on a bun.", category="Burgers", price=10.99, is_available=True),
        MenuItems(item_name="Bacon Cheeseburger", description="Beef patty, cheese, bacon, lettuce, tomato, and onion on a bun.", category="Burgers", price=12.99, is_available=True),
        MenuItems(item_name="Fries", description="Classic French fries.", category="Sides", price=4.99, is_available=True),
        MenuItems(item_name="Onion Rings", description="Crispy fried onion rings.", category="Sides", price=5.99, is_available=True),
        MenuItems(item_name="Coca-Cola", description="Classic Coca-Cola.", category="Drinks", price=2.99, is_available=True),
        MenuItems(item_name="Sprite", description="Lemon-lime soda.", category="Drinks", price=2.99, is_available=True),
        MenuItems(item_name="Iced Tea", description="Freshly brewed iced tea.", category="Drinks", price=3.49, is_available=True),
        MenuItems(item_name="Chocolate Cake", description="Rich chocolate cake.", category="Desserts", price=6.99, is_available=True),
        MenuItems(item_name="Ice Cream", description="Vanilla ice cream.", category="Desserts", price=4.99, is_available=True),
    ]
    session.add_all(menu_items)
    session.commit()

    # Sample Staff Members
    staff_members = [
        Staff(first_name="Alice", last_name="Smith", position="Manager", hire_date=datetime.date(2020, 1, 15), salary=60000),
        Staff(first_name="Bob", last_name="Johnson", position="Chef", hire_date=datetime.date(2021, 5, 20), salary=50000),
        Staff(first_name="Charlie", last_name="Brown", position="Waiter", hire_date=datetime.date(2022, 9, 10), salary=35000),
        Staff(first_name="David", last_name="Lee", position="Waiter", hire_date=datetime.date(2023, 1, 5), salary=36000),
    ]
    session.add_all(staff_members)
    session.commit()

    # Sample Customers
    customers = [
        Customers(first_name="Eve", last_name="Williams", phone_number="555-123-4567", email="eve.williams@example.com"),
        Customers(first_name="Frank", last_name="Davis", phone_number="555-987-6543", email="frank.davis@example.com"),
        Customers(first_name="Grace", last_name="Miller", phone_number="555-246-8013", email="grace.miller@example.com"),
        Customers(first_name="Henry", last_name="Wilson", phone_number="555-135-7924", email="henry.wilson@example.com"),
        Customers(first_name="Ivy", last_name="Moore", phone_number="555-864-2097", email="ivy.moore@example.com"),
    ]
    session.add_all(customers)
    session.commit()

    # Sample Orders
    orders = []
    for i in range(10):
        customer = random.choice(customers)
        staff = random.choice(staff_members)
        order_date = datetime.datetime.now() - datetime.timedelta(days=random.randint(0, 30))
        payment_method = random.choice(["Credit Card", "Cash", "Online Payment"])
        order_status = random.choice(["Received", "Processing", "Shipped", "Delivered"])
        orders.append(Orders(customer_id=customer.customer_id, staff_id=staff.staff_id, order_date=order_date, total_amount=0, payment_method=payment_method, order_status=order_status))

    session.add_all(orders)
    session.commit()

    # Sample Order Items
    order_items = []
    for order in orders:
        num_items = random.randint(1, 4)
        total_amount = 0
        for _ in range(num_items):
            menu_item = random.choice(menu_items)
            quantity = random.randint(1, 3)
            item_price = menu_item.price
            total_amount += item_price * quantity
            order_items.append(OrderItems(order_id=order.order_id, menu_item_id=menu_item.menu_item_id, quantity=quantity, item_price=item_price))
        order.total_amount = total_amount
    session.add_all(order_items)
    session.commit()



if __name__ == '__main__':
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    populate(engine)

    Session = sessionmaker(bind=engine)
    session = Session()

    # Example query to verify data population
    first_customer = session.query(Customers).first()
    print(f"First customer: {first_customer.first_name} {first_customer.last_name}")

    first_order = session.query(Orders).first()
    print(f"First order total amount: {first_order.total_amount}")
