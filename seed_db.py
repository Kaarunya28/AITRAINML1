"""
Seed the SQLite database from the generated CSV files.
Run AFTER: python data/generate_data.py
       AND: python ml/train_models.py
"""

import os, sys
sys.path.insert(0, os.path.dirname(__file__))

import pandas as pd
from app.database import SessionLocal, engine, Base
from app.models.models import Customer, Product, Order, OrderItem, CustomerActivity, User
from app.auth import hash_password

Base.metadata.create_all(bind=engine)

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
db = SessionLocal()


def _clear():
    print("Clearing existing data …")
    db.query(CustomerActivity).delete()
    db.query(OrderItem).delete()
    db.query(Order).delete()
    db.query(Customer).delete()
    db.query(Product).delete()
    db.query(User).delete()
    db.commit()


def seed_users():
    print("Creating admin user …")
    admin = User(
        email           = "admin@smartcart.com",
        hashed_password = hash_password("admin123"),
        role            = "admin",
    )
    db.add(admin)
    db.commit()
    print("  admin@smartcart.com / admin123")


def seed_customers():
    print("Seeding customers …")
    df = pd.read_csv(os.path.join(DATA_DIR, "customers_clean.csv"))
    seg_path = os.path.join(DATA_DIR, "customer_segments.csv")
    if os.path.exists(seg_path):
        segs = pd.read_csv(seg_path).set_index("customer_id")["segment"].to_dict()
    else:
        segs = {}

    for _, row in df.iterrows():
        cust = Customer(
            customer_id         = int(row["customer_id"]),
            name                = str(row["name"]),
            email               = str(row["email"]),
            age                 = int(row["age"]),
            gender              = str(row.get("gender", "Other")),
            city                = str(row.get("city", "")),
            phone               = str(row.get("phone", "")),
            total_purchases     = int(row.get("total_purchases", 0)),
            total_spending      = float(row.get("total_spending", 0)),
            average_order_value = float(row.get("average_order_value", 0)),
            website_visits      = int(row.get("website_visits", 0)),
            segment             = segs.get(int(row["customer_id"]), "New Customer"),
        )
        db.add(cust)
    db.commit()
    print(f"  {len(df)} customers added")


def seed_products():
    print("Seeding products …")
    df = pd.read_csv(os.path.join(DATA_DIR, "products_clean.csv"))
    for _, row in df.iterrows():
        prod = Product(
            product_id   = int(row["product_id"]),
            product_name = str(row["product_name"]),
            category     = str(row["category"]),
            price        = float(row["price"]),
            rating       = float(row.get("rating", 0)),
            stock        = int(row.get("stock", 0)),
            discount     = float(row.get("discount", 0)),
            description  = str(row.get("description", "")),
        )
        db.add(prod)
    db.commit()
    print(f"  {len(df)} products added")


def seed_orders():
    print("Seeding orders …")
    df = pd.read_csv(os.path.join(DATA_DIR, "orders_clean.csv"))
    valid_cids = {c.customer_id for c in db.query(Customer).all()}
    valid_pids = {p.product_id  for p in db.query(Product).all()}

    order_map = {}
    for _, row in df.iterrows():
        cid = int(row["customer_id"])
        pid = int(row["product_id"])
        if cid not in valid_cids or pid not in valid_pids:
            continue
        oid = int(row["order_id"])
        order = Order(
            order_id        = oid,
            customer_id     = cid,
            total_amount    = float(row["price"]),
            payment_method  = str(row.get("payment_method", "cash_on_delivery")),
            order_status    = str(row.get("order_status", "delivered")),
        )
        db.add(order)
        order_map[oid] = {"product_id": pid, "quantity": int(row.get("quantity", 1)),
                          "price": float(row["price"])}

    db.flush()
    for oid, info in order_map.items():
        db.add(OrderItem(
            order_id   = oid,
            product_id = info["product_id"],
            quantity   = info["quantity"],
            price      = info["price"],
        ))
    db.commit()
    print(f"  {len(order_map)} orders added")


def seed_activity():
    print("Seeding customer activity …")
    df = pd.read_csv(os.path.join(DATA_DIR, "activity_clean.csv"))
    valid_cids = {c.customer_id for c in db.query(Customer).all()}
    valid_pids = {p.product_id  for p in db.query(Product).all()}
    count = 0
    for _, row in df.iterrows():
        cid = int(row["customer_id"])
        pid = int(row["product_id"])
        if cid not in valid_cids or pid not in valid_pids:
            continue
        db.add(CustomerActivity(
            customer_id        = cid,
            product_id         = pid,
            product_views      = int(row.get("product_views", 0)),
            cart_additions     = int(row.get("cart_additions", 0)),
            wishlist_additions = int(row.get("wishlist_additions", 0)),
            previous_purchases = int(row.get("previous_purchases", 0)),
            time_spent         = float(row.get("time_spent", 0)),
            purchased          = int(row.get("purchased", 0)),
        ))
        count += 1
    db.commit()
    print(f"  {count} activity records added")


if __name__ == "__main__":
    _clear()
    seed_users()
    seed_customers()
    seed_products()
    seed_orders()
    seed_activity()
    db.close()
    print("\n✓ Database seeded successfully!")
    print("  Login: admin@smartcart.com / admin123")
