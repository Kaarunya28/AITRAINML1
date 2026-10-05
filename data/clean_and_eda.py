"""
Step 3 & 4 – Data Cleaning + Exploratory Data Analysis
Run:  python data/clean_and_eda.py
Outputs charts to data/plots/
"""

import os
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")          # headless – works on servers too
import matplotlib.pyplot as plt
import seaborn as sns

DATA_DIR  = os.path.dirname(__file__)
PLOTS_DIR = os.path.join(DATA_DIR, "plots")
os.makedirs(PLOTS_DIR, exist_ok=True)

sns.set_theme(style="whitegrid")

# ─────────────────────────────────────────────
#  LOAD
# ─────────────────────────────────────────────
customers = pd.read_csv(os.path.join(DATA_DIR, "customers.csv"))
products  = pd.read_csv(os.path.join(DATA_DIR, "products.csv"))
orders    = pd.read_csv(os.path.join(DATA_DIR, "orders.csv"))
activity  = pd.read_csv(os.path.join(DATA_DIR, "customer_activity.csv"))

print("=" * 60)
print("STEP 3 – DATA CLEANING")
print("=" * 60)

# ─────────────────────────────────────────────
#  MISSING VALUES
# ─────────────────────────────────────────────
for name, df in [("Customers", customers), ("Products", products),
                 ("Orders", orders), ("Activity", activity)]:
    mv = df.isnull().sum()
    if mv.any():
        print(f"\n[{name}] Missing values:\n{mv[mv > 0]}")
    else:
        print(f"[{name}] No missing values ✓")

# Fill missing ratings with median
if products["rating"].isnull().any():
    products["rating"].fillna(products["rating"].median(), inplace=True)
    print("  → Missing ratings filled with median")

# ─────────────────────────────────────────────
#  DUPLICATES
# ─────────────────────────────────────────────
for name, df, key in [
    ("Customers", customers, "customer_id"),
    ("Products",  products,  "product_id"),
    ("Orders",    orders,    "order_id"),
]:
    dups = df.duplicated(subset=[key]).sum()
    print(f"[{name}] Duplicate {key}: {dups}")
    if dups:
        df.drop_duplicates(subset=[key], keep="first", inplace=True)

# ─────────────────────────────────────────────
#  DATA TYPES
# ─────────────────────────────────────────────
customers["registration_date"] = pd.to_datetime(customers["registration_date"], errors="coerce")
orders["order_date"]           = pd.to_datetime(orders["order_date"],           errors="coerce")
products["price"]              = pd.to_numeric(products["price"],  errors="coerce")
products["rating"]             = pd.to_numeric(products["rating"], errors="coerce")
orders["price"]                = pd.to_numeric(orders["price"],    errors="coerce")
customers["age"]               = pd.to_numeric(customers["age"],   errors="coerce")
print("\nData types corrected ✓")

# ─────────────────────────────────────────────
#  INVALID VALUES
# ─────────────────────────────────────────────
invalid_price  = products[products["price"] <= 0]
invalid_age    = customers[(customers["age"] < 18) | (customers["age"] > 100)]
invalid_rating = products[(products["rating"] < 0) | (products["rating"] > 5)]

print(f"\nInvalid prices   : {len(invalid_price)}")
print(f"Invalid ages     : {len(invalid_age)}")
print(f"Invalid ratings  : {len(invalid_rating)}")

# Drop invalid prices; clip ages
products = products[products["price"] > 0]
customers["age"] = customers["age"].clip(18, 100)
products["rating"] = products["rating"].clip(0, 5)

# ─────────────────────────────────────────────
#  INVALID FK REFERENCES
# ─────────────────────────────────────────────
valid_cids = set(customers["customer_id"])
valid_pids = set(products["product_id"])

bad_orders = orders[
    ~orders["customer_id"].isin(valid_cids) |
    ~orders["product_id"].isin(valid_pids)
]
print(f"\nOrders with invalid IDs : {len(bad_orders)}")
orders = orders[
    orders["customer_id"].isin(valid_cids) &
    orders["product_id"].isin(valid_pids)
]

bad_act = activity[
    ~activity["customer_id"].isin(valid_cids) |
    ~activity["product_id"].isin(valid_pids)
]
print(f"Activity with invalid IDs : {len(bad_act)}")
activity = activity[
    activity["customer_id"].isin(valid_cids) &
    activity["product_id"].isin(valid_pids)
]

# ─────────────────────────────────────────────
#  BASIC STATS
# ─────────────────────────────────────────────
print("\n── Customers ──")
print(customers[["age","total_purchases","total_spending","website_visits"]].describe().round(2))

print("\n── Products ──")
print(products[["price","rating","stock","discount"]].describe().round(2))

print("\n── Orders ──")
print(orders[["quantity","price"]].describe().round(2))

# Save cleaned CSVs
customers.to_csv(os.path.join(DATA_DIR, "customers_clean.csv"), index=False)
products.to_csv(os.path.join(DATA_DIR,  "products_clean.csv"),  index=False)
orders.to_csv(os.path.join(DATA_DIR,    "orders_clean.csv"),    index=False)
activity.to_csv(os.path.join(DATA_DIR,  "activity_clean.csv"),  index=False)
print("\nCleaned CSVs saved ✓")

# ─────────────────────────────────────────────
#  STEP 4 – EDA
# ─────────────────────────────────────────────
print("\n" + "=" * 60)
print("STEP 4 – EXPLORATORY DATA ANALYSIS")
print("=" * 60)

# Join orders with products
orders_full = orders.merge(products[["product_id","product_name","category","price"]]
                           .rename(columns={"price":"unit_price"}),
                           on="product_id", how="left")
orders_full = orders_full.merge(customers[["customer_id","name","city"]],
                                on="customer_id", how="left")

# 1. Category with highest sales
cat_sales = orders_full.groupby("category")["price"].sum().sort_values(ascending=False)
print(f"\n1. Top category by revenue: {cat_sales.idxmax()} (₹{cat_sales.max():,.0f})")

fig, ax = plt.subplots(figsize=(10, 5))
cat_sales.plot(kind="bar", color="steelblue", ax=ax)
ax.set_title("Revenue by Category"); ax.set_ylabel("Total Revenue (₹)")
plt.xticks(rotation=45, ha="right"); plt.tight_layout()
fig.savefig(os.path.join(PLOTS_DIR, "01_revenue_by_category.png"))
plt.close()

# 2. Top 10 products by revenue
prod_rev = orders_full.groupby("product_name")["price"].sum().nlargest(10)
print(f"\n2. Top product: {prod_rev.idxmax()} (₹{prod_rev.max():,.0f})")

fig, ax = plt.subplots(figsize=(10, 5))
prod_rev.sort_values().plot(kind="barh", color="darkorange", ax=ax)
ax.set_title("Top 10 Products by Revenue"); ax.set_xlabel("Revenue (₹)")
plt.tight_layout(); fig.savefig(os.path.join(PLOTS_DIR, "02_top_products_revenue.png")); plt.close()

# 3. Top 10 customers by spending
cust_spend = orders_full.groupby("name")["price"].sum().nlargest(10)
print(f"\n3. Top customer: {cust_spend.idxmax()} (₹{cust_spend.max():,.0f})")

fig, ax = plt.subplots(figsize=(10, 5))
cust_spend.sort_values().plot(kind="barh", color="seagreen", ax=ax)
ax.set_title("Top 10 Customers by Spending"); ax.set_xlabel("Total Spending (₹)")
plt.tight_layout(); fig.savefig(os.path.join(PLOTS_DIR, "03_top_customers_spending.png")); plt.close()

# 4. Average order value
aov = orders_full["price"].mean()
print(f"\n4. Average order value: ₹{aov:,.2f}")

# 5. Payment method distribution
pm_counts = orders_full["payment_method"].value_counts()
print(f"\n5. Most used payment: {pm_counts.idxmax()} ({pm_counts.max()} orders)")

fig, ax = plt.subplots(figsize=(7, 7))
pm_counts.plot(kind="pie", autopct="%1.1f%%", ax=ax, startangle=90)
ax.set_title("Payment Method Distribution"); ax.set_ylabel("")
plt.tight_layout(); fig.savefig(os.path.join(PLOTS_DIR, "04_payment_methods.png")); plt.close()

# 6. City with highest customers
city_counts = customers["city"].value_counts()
print(f"\n6. Top city: {city_counts.idxmax()} ({city_counts.max()} customers)")

fig, ax = plt.subplots(figsize=(9, 5))
city_counts.plot(kind="bar", color="purple", ax=ax)
ax.set_title("Customers by City"); ax.set_ylabel("Count")
plt.xticks(rotation=30); plt.tight_layout()
fig.savefig(os.path.join(PLOTS_DIR, "05_customers_by_city.png")); plt.close()

# 7. Top rated products
top_rated = products.nlargest(10, "rating")[["product_name","rating"]]
print(f"\n7. Highest rated: {top_rated.iloc[0]['product_name']} ({top_rated.iloc[0]['rating']})")

fig, ax = plt.subplots(figsize=(10, 5))
ax.barh(top_rated["product_name"], top_rated["rating"], color="gold")
ax.set_title("Top 10 Highest Rated Products"); ax.set_xlabel("Rating")
plt.tight_layout(); fig.savefig(os.path.join(PLOTS_DIR, "06_top_rated_products.png")); plt.close()

# 8. Repeat purchase percentage
repeat = customers[customers["total_purchases"] > 1]
pct = len(repeat) / len(customers) * 100
print(f"\n8. Customers with repeat purchases: {pct:.1f}%")

# 9. Monthly revenue
orders_full["month"] = pd.to_datetime(orders_full["order_date"]).dt.to_period("M")
monthly = orders_full.groupby("month")["price"].sum()
print(f"\n9. Monthly revenue (last 6 months):\n{monthly.tail(6)}")

fig, ax = plt.subplots(figsize=(12, 5))
monthly.plot(ax=ax, marker="o", color="teal")
ax.set_title("Monthly Revenue Trend"); ax.set_ylabel("Revenue (₹)")
plt.xticks(rotation=45); plt.tight_layout()
fig.savefig(os.path.join(PLOTS_DIR, "07_monthly_revenue.png")); plt.close()

# 10. Low stock products (< 20)
low_stock = products[products["stock"] < 20][["product_name","category","stock"]]
print(f"\n10. Low stock products ({len(low_stock)}):\n{low_stock.to_string(index=False)}")

fig, ax = plt.subplots(figsize=(10, 5))
ax.barh(low_stock["product_name"], low_stock["stock"], color="crimson")
ax.set_title("Low Stock Products (< 20 units)"); ax.set_xlabel("Stock")
plt.tight_layout(); fig.savefig(os.path.join(PLOTS_DIR, "08_low_stock.png")); plt.close()

# Correlation heatmap for activity
fig, ax = plt.subplots(figsize=(9, 7))
sns.heatmap(activity[["product_views","cart_additions","wishlist_additions",
                        "previous_purchases","time_spent","purchased"]].corr(),
            annot=True, fmt=".2f", cmap="coolwarm", ax=ax)
ax.set_title("Feature Correlation (Customer Activity)")
plt.tight_layout(); fig.savefig(os.path.join(PLOTS_DIR, "09_correlation_heatmap.png")); plt.close()

print(f"\nAll plots saved to {PLOTS_DIR}")
print("\n✓ Data Cleaning & EDA complete")
