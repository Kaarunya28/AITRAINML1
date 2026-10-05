"""
Step 9 – Recommendation System
Content-based + collaborative-filtering hybrid.
"""

import os
import joblib
import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import MinMaxScaler

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
ML_DIR   = os.path.dirname(__file__)


def _load_data():
    customers = pd.read_csv(os.path.join(DATA_DIR, "customers_clean.csv"))
    products  = pd.read_csv(os.path.join(DATA_DIR, "products_clean.csv"))
    try:
        activity  = pd.read_csv(os.path.join(DATA_DIR, "activity_clean.csv"))
    except FileNotFoundError:
        activity  = pd.read_csv(os.path.join(DATA_DIR, "customer_activity.csv"))
    return customers, products, activity


def get_recommendations(customer_id: int, top_n: int = 5) -> list[dict]:
    """
    Returns top-N product recommendations for a given customer.
    Strategy:
      1. Find products the customer has NOT purchased.
      2. Score each by:
         - rating weight (40 %)
         - category affinity  (30 %)
         - collaborative popularity (30 %)
      3. Return top-N.
    """
    customers, products, activity = _load_data()

    # Products the customer already bought
    bought_pids = set(
        activity.loc[
            (activity["customer_id"] == customer_id) & (activity["purchased"] == 1),
            "product_id"
        ]
    )

    # Candidate products
    candidates = products[~products["product_id"].isin(bought_pids)].copy()
    if candidates.empty:
        candidates = products.copy()   # fallback – recommend everything

    # ── Category affinity ────────────────────────────────────────────────
    cust_activity = activity[activity["customer_id"] == customer_id]
    liked_pids    = set(cust_activity.loc[cust_activity["previous_purchases"] > 0, "product_id"])
    liked_cats    = products.loc[products["product_id"].isin(liked_pids), "category"].value_counts()
    total_liked   = liked_cats.sum() if liked_cats.sum() > 0 else 1

    def cat_score(cat):
        return liked_cats.get(cat, 0) / total_liked

    candidates["cat_score"] = candidates["category"].apply(cat_score)

    # ── Popularity (collaborative proxy) ─────────────────────────────────
    pop = (activity.groupby("product_id")["purchased"].sum()
           .reset_index().rename(columns={"purchased": "pop"}))
    candidates = candidates.merge(pop, on="product_id", how="left").fillna({"pop": 0})
    max_pop = candidates["pop"].max() if candidates["pop"].max() > 0 else 1
    candidates["pop_score"] = candidates["pop"] / max_pop

    # ── Normalise rating ─────────────────────────────────────────────────
    candidates["rating_norm"] = candidates["rating"] / 5.0

    # ── Final score ───────────────────────────────────────────────────────
    candidates["score"] = (
        0.40 * candidates["rating_norm"] +
        0.30 * candidates["cat_score"]   +
        0.30 * candidates["pop_score"]
    )

    top = candidates.nlargest(top_n, "score")[
        ["product_id", "product_name", "category", "price", "rating", "score"]
    ].reset_index(drop=True)

    return top.to_dict(orient="records")


def get_similar_products(product_id: int, top_n: int = 5) -> list[dict]:
    """Returns similar products based on category, price, and rating."""
    _, products, _ = _load_data()

    features = products[["price", "rating", "discount"]].fillna(0)
    scaler   = MinMaxScaler()
    feat_sc  = scaler.fit_transform(features)

    sim_matrix = cosine_similarity(feat_sc)
    if product_id not in products["product_id"].values:
        return []

    idx   = products.index[products["product_id"] == product_id][0]
    sims  = list(enumerate(sim_matrix[idx]))
    sims  = sorted(sims, key=lambda x: x[1], reverse=True)[1:top_n + 1]
    rows  = [products.iloc[i] for i, _ in sims]
    scores = [s for _, s in sims]

    results = []
    for row, score in zip(rows, scores):
        results.append({
            "product_id"  : int(row["product_id"]),
            "product_name": row["product_name"],
            "category"    : row["category"],
            "price"       : float(row["price"]),
            "rating"      : float(row["rating"]),
            "score"       : round(float(score), 4),
        })
    return results
