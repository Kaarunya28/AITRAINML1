"""
Generate synthetic datasets for SmartCart:
  - customers.csv   (100+ records)
  - products.csv    (50+ records)
  - orders.csv      (500+ records)
  - customer_activity.csv
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import os

random.seed(42)
np.random.seed(42)

OUTPUT_DIR = os.path.dirname(__file__)

# ─────────────────────────────────────────────
#  HELPER
# ─────────────────────────────────────────────
def random_date(start: datetime, end: datetime) -> str:
    delta = end - start
    return (start + timedelta(seconds=random.randint(0, int(delta.total_seconds())))).strftime("%Y-%m-%d")


# ─────────────────────────────────────────────
#  CUSTOMERS  (120 records)
# ─────────────────────────────────────────────
def generate_customers(n: int = 120) -> pd.DataFrame:
    genders = ["Male", "Female", "Other"]
    cities  = ["Mumbai", "Delhi", "Bangalore", "Chennai", "Hyderabad",
               "Kolkata", "Pune", "Ahmedabad", "Jaipur", "Surat"]

    first_names = ["Aarav","Vivaan","Aditya","Sai","Arjun","Krishna","Rohan","Dhruv",
                   "Ananya","Priya","Sakshi","Pooja","Neha","Sneha","Kavya","Meera",
                   "Rahul","Vikram","Amit","Suresh","Ravi","Karan","Nikhil","Mohit",
                   "Anjali","Shreya","Divya","Riya","Simran","Tanvi"]
    last_names  = ["Sharma","Verma","Patel","Singh","Kumar","Gupta","Joshi","Mehta",
                   "Nair","Rao","Iyer","Reddy","Bose","Das","Pillai","Chopra"]

    records = []
    for i in range(1, n + 1):
        tp  = random.randint(0, 50)
        ts  = round(tp * random.uniform(300, 5000), 2)
        aov = round(ts / tp, 2) if tp > 0 else 0.0
        records.append({
            "customer_id"        : i,
            "name"               : f"{random.choice(first_names)} {random.choice(last_names)}",
            "email"              : f"customer{i}@smartcart.com",
            "age"                : random.randint(18, 65),
            "gender"             : random.choice(genders),
            "city"               : random.choice(cities),
            "phone"              : f"+91-{random.randint(7000000000, 9999999999)}",
            "registration_date"  : random_date(datetime(2021, 1, 1), datetime(2024, 1, 1)),
            "total_purchases"    : tp,
            "total_spending"     : ts,
            "average_order_value": aov,
            "website_visits"     : random.randint(1, 200),
        })

    return pd.DataFrame(records)


# ─────────────────────────────────────────────
#  PRODUCTS  (55 records)
# ─────────────────────────────────────────────
def generate_products(n: int = 55) -> pd.DataFrame:
    catalogue = [
        ("Wireless Headphones","Electronics"),("Smart Watch","Electronics"),
        ("Laptop Stand","Electronics"),("USB-C Hub","Electronics"),
        ("Bluetooth Speaker","Electronics"),("Gaming Mouse","Electronics"),
        ("Mechanical Keyboard","Electronics"),("Webcam HD","Electronics"),
        ("Power Bank 20000mAh","Electronics"),("LED Desk Lamp","Electronics"),
        ("Running Shoes","Footwear"),("Casual Sneakers","Footwear"),
        ("Formal Leather Shoes","Footwear"),("Sandals","Footwear"),
        ("Sports Socks","Footwear"),
        ("Men's T-Shirt","Clothing"),("Women's Kurti","Clothing"),
        ("Denim Jeans","Clothing"),("Winter Jacket","Clothing"),
        ("Yoga Pants","Clothing"),("Formal Shirt","Clothing"),
        ("Saree","Clothing"),("Kids Dress","Clothing"),
        ("Protein Powder","Health & Fitness"),("Yoga Mat","Health & Fitness"),
        ("Resistance Bands","Health & Fitness"),("Jump Rope","Health & Fitness"),
        ("Water Bottle","Health & Fitness"),
        ("Non-Stick Pan","Kitchen"),("Mixer Grinder","Kitchen"),
        ("Air Fryer","Kitchen"),("Coffee Maker","Kitchen"),
        ("Rice Cooker","Kitchen"),("Knife Set","Kitchen"),
        ("The Alchemist (Book)","Books"),("Atomic Habits (Book)","Books"),
        ("Python Programming","Books"),("Data Science Handbook","Books"),
        ("Moisturizer SPF30","Beauty"),("Face Wash","Beauty"),
        ("Hair Serum","Beauty"),("Sunscreen","Beauty"),
        ("Lipstick Set","Beauty"),
        ("Sofa Cover","Home Decor"),("Curtains","Home Decor"),
        ("Wall Clock","Home Decor"),("Photo Frame Set","Home Decor"),
        ("Scented Candles","Home Decor"),
        ("LEGO Set","Toys"),("Remote Control Car","Toys"),
        ("Board Game","Toys"),("Puzzle 1000pc","Toys"),
        ("Action Figure","Toys"),("Doll House","Toys"),
        ("Cricket Bat","Sports"),
    ]

    records = []
    for i, (name, cat) in enumerate(catalogue[:n], start=1):
        price    = round(random.uniform(99, 9999), 2)
        discount = round(random.uniform(0, 40), 1)
        records.append({
            "product_id"  : i,
            "product_name": name,
            "category"    : cat,
            "price"       : price,
            "rating"      : round(random.uniform(2.5, 5.0), 1),
            "stock"       : random.randint(0, 500),
            "discount"    : discount,
            "description" : f"High quality {name} available at SmartCart.",
        })

    return pd.DataFrame(records)


# ─────────────────────────────────────────────
#  ORDERS  (600 records)
# ─────────────────────────────────────────────
def generate_orders(customers: pd.DataFrame, products: pd.DataFrame,
                    n: int = 600) -> pd.DataFrame:
    statuses  = ["pending","confirmed","shipped","delivered","cancelled"]
    payments  = ["credit_card","debit_card","paypal","upi","cash_on_delivery"]
    weights   = [0.1, 0.2, 0.2, 0.4, 0.1]

    records = []
    for i in range(1, n + 1):
        cust    = customers.sample(1).iloc[0]
        prod    = products.sample(1).iloc[0]
        qty     = random.randint(1, 5)
        price   = round(prod["price"] * (1 - prod["discount"] / 100) * qty, 2)
        records.append({
            "order_id"      : i,
            "customer_id"   : int(cust["customer_id"]),
            "product_id"    : int(prod["product_id"]),
            "quantity"      : qty,
            "order_date"    : random_date(datetime(2022, 1, 1), datetime(2024, 6, 1)),
            "price"         : price,
            "payment_method": random.choice(payments),
            "order_status"  : random.choices(statuses, weights)[0],
        })

    return pd.DataFrame(records)


# ─────────────────────────────────────────────
#  CUSTOMER ACTIVITY
# ─────────────────────────────────────────────
def generate_activity(customers: pd.DataFrame, products: pd.DataFrame) -> pd.DataFrame:
    records = []
    for _, cust in customers.iterrows():
        sampled = products.sample(random.randint(5, 15))
        for _, prod in sampled.iterrows():
            views  = random.randint(0, 20)
            cart   = random.randint(0, min(views, 5))
            wish   = random.randint(0, 3)
            prev   = random.randint(0, 5)
            spent  = round(random.uniform(0, 30), 1)
            # purchase more likely if high engagement
            score  = views * 0.3 + cart * 1.5 + prev * 2.0 + spent * 0.1
            prob   = min(score / 20, 0.95)
            purchased = 1 if random.random() < prob else 0
            records.append({
                "customer_id"       : int(cust["customer_id"]),
                "product_id"        : int(prod["product_id"]),
                "product_views"     : views,
                "cart_additions"    : cart,
                "wishlist_additions": wish,
                "previous_purchases": prev,
                "time_spent"        : spent,
                "purchased"         : purchased,
            })

    return pd.DataFrame(records)


# ─────────────────────────────────────────────
#  MAIN
# ─────────────────────────────────────────────
if __name__ == "__main__":
    print("Generating datasets …")

    customers = generate_customers()
    products  = generate_products()
    orders    = generate_orders(customers, products)
    activity  = generate_activity(customers, products)

    customers.to_csv(os.path.join(OUTPUT_DIR, "customers.csv"), index=False)
    products.to_csv(os.path.join(OUTPUT_DIR, "products.csv"),   index=False)
    orders.to_csv(os.path.join(OUTPUT_DIR, "orders.csv"),       index=False)
    activity.to_csv(os.path.join(OUTPUT_DIR, "customer_activity.csv"), index=False)

    print(f"  customers        : {len(customers)} rows")
    print(f"  products         : {len(products)} rows")
    print(f"  orders           : {len(orders)} rows")
    print(f"  customer_activity: {len(activity)} rows")
    print("Done — CSVs saved to data/")
