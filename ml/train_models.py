"""
Step 5-8 – Feature Engineering + Model Training
  • Purchase Prediction  → ml/purchase_model.pkl
  • Customer Segmentation → ml/segmentation_model.pkl
  • Label Encoder / Scaler objects also saved

Run:  python ml/train_models.py
"""

import os, warnings
warnings.filterwarnings("ignore")

import pandas as pd
import numpy as np
import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score,
    f1_score, confusion_matrix, roc_auc_score,
    ConfusionMatrixDisplay, roc_curve
)
from sklearn.cluster import KMeans
from sklearn.pipeline import Pipeline

DATA_DIR  = os.path.join(os.path.dirname(__file__), "..", "data")
ML_DIR    = os.path.dirname(__file__)
PLOTS_DIR = os.path.join(DATA_DIR, "plots")
os.makedirs(PLOTS_DIR, exist_ok=True)

# ─────────────────────────────────────────────
#  STEP 5 – FEATURE ENGINEERING
# ─────────────────────────────────────────────
print("=" * 60)
print("STEP 5 – FEATURE ENGINEERING")
print("=" * 60)

customers = pd.read_csv(os.path.join(DATA_DIR, "customers_clean.csv"))
products  = pd.read_csv(os.path.join(DATA_DIR, "products_clean.csv"))
activity  = pd.read_csv(os.path.join(DATA_DIR, "activity_clean.csv"))

# Merge customer features
ml_df = activity.merge(
    customers[["customer_id","age","total_purchases","total_spending",
               "average_order_value","website_visits"]],
    on="customer_id", how="left"
)
# Merge product features
ml_df = ml_df.merge(
    products[["product_id","price","rating"]].rename(
        columns={"price":"product_price","rating":"product_rating"}),
    on="product_id", how="left"
)

FEATURES = [
    "age","total_purchases","total_spending","average_order_value",
    "website_visits","product_price","product_rating",
    "product_views","cart_additions","wishlist_additions",
    "previous_purchases","time_spent",
]
TARGET = "purchased"

ml_df = ml_df.dropna(subset=FEATURES + [TARGET])
X = ml_df[FEATURES]
y = ml_df[TARGET].astype(int)

print(f"Dataset shape  : {X.shape}")
print(f"Purchase rate  : {y.mean()*100:.1f}%")

# ─────────────────────────────────────────────
#  STEP 6 – MODEL TRAINING & COMPARISON
# ─────────────────────────────────────────────
print("\n" + "=" * 60)
print("STEP 6 – PURCHASE PREDICTION MODELS")
print("=" * 60)

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

scaler = StandardScaler()
X_train_sc = scaler.fit_transform(X_train)
X_test_sc  = scaler.transform(X_test)

# --- Three classifiers ---
classifiers = {
    "Logistic Regression": LogisticRegression(max_iter=1000, random_state=42),
    "Decision Tree"      : DecisionTreeClassifier(max_depth=8, random_state=42),
    "Random Forest"      : RandomForestClassifier(n_estimators=100, random_state=42,
                                                   n_jobs=-1),
}

results = {}
for name, clf in classifiers.items():
    if name == "Logistic Regression":
        clf.fit(X_train_sc, y_train)
        y_pred = clf.predict(X_test_sc)
        y_prob = clf.predict_proba(X_test_sc)[:, 1]
    else:
        clf.fit(X_train, y_train)
        y_pred = clf.predict(X_test)
        y_prob = clf.predict_proba(X_test)[:, 1]

    results[name] = {
        "accuracy" : accuracy_score(y_test, y_pred),
        "precision": precision_score(y_test, y_pred, zero_division=0),
        "recall"   : recall_score(y_test, y_pred, zero_division=0),
        "f1"       : f1_score(y_test, y_pred, zero_division=0),
        "roc_auc"  : roc_auc_score(y_test, y_prob),
        "cm"       : confusion_matrix(y_test, y_pred),
        "model"    : clf,
        "y_prob"   : y_prob,
    }

# Print comparison table
print(f"\n{'Model':<22} {'Accuracy':>9} {'Precision':>10} {'Recall':>8} {'F1':>8} {'ROC-AUC':>9}")
print("-" * 70)
for name, r in results.items():
    print(f"{name:<22} {r['accuracy']:>9.4f} {r['precision']:>10.4f} "
          f"{r['recall']:>8.4f} {r['f1']:>8.4f} {r['roc_auc']:>9.4f}")

# Confusion matrices
fig, axes = plt.subplots(1, 3, figsize=(16, 5))
for ax, (name, r) in zip(axes, results.items()):
    ConfusionMatrixDisplay(r["cm"]).plot(ax=ax, colorbar=False)
    ax.set_title(name)
plt.suptitle("Confusion Matrices – Purchase Prediction", y=1.02)
plt.tight_layout()
fig.savefig(os.path.join(PLOTS_DIR, "10_confusion_matrices.png"), bbox_inches="tight")
plt.close()

# ROC curves
fig, ax = plt.subplots(figsize=(8, 6))
for name, r in results.items():
    fpr, tpr, _ = roc_curve(y_test, r["y_prob"])
    ax.plot(fpr, tpr, label=f"{name} (AUC={r['roc_auc']:.3f})")
ax.plot([0,1],[0,1],"k--"); ax.set_xlabel("FPR"); ax.set_ylabel("TPR")
ax.set_title("ROC Curves"); ax.legend(); plt.tight_layout()
fig.savefig(os.path.join(PLOTS_DIR, "11_roc_curves.png")); plt.close()

# ─────────────────────────────────────────────
#  STEP 7 – SAVE BEST MODEL
# ─────────────────────────────────────────────
print("\n" + "=" * 60)
print("STEP 7 – MODEL SELECTION & SAVING")
print("=" * 60)

best_name = max(results, key=lambda k: results[k]["f1"])
print(f"Best model: {best_name} (F1={results[best_name]['f1']:.4f})")

best_clf  = results[best_name]["model"]

# For Logistic Regression we need scaled input; for tree-based we don't
# We'll build a unified pipeline for easy inference
if best_name == "Logistic Regression":
    pipeline = Pipeline([("scaler", scaler),
                         ("clf", best_clf)])
else:
    # Still wrap in pipeline so inference is uniform (scaler is a passthrough)
    from sklearn.preprocessing import FunctionTransformer
    identity = FunctionTransformer()
    pipeline = Pipeline([("scaler", identity),
                         ("clf", best_clf)])

# Feature importance for Random Forest
if best_name == "Random Forest":
    fi = pd.Series(best_clf.feature_importances_, index=FEATURES).sort_values(ascending=False)
    fig, ax = plt.subplots(figsize=(9, 5))
    fi.plot(kind="bar", color="steelblue", ax=ax)
    ax.set_title("Feature Importances – Random Forest"); ax.set_ylabel("Importance")
    plt.xticks(rotation=45, ha="right"); plt.tight_layout()
    fig.savefig(os.path.join(PLOTS_DIR, "12_feature_importance.png")); plt.close()

# Save artifacts
joblib.dump(best_clf,                    os.path.join(ML_DIR, "purchase_model.pkl"))
joblib.dump(scaler,                      os.path.join(ML_DIR, "scaler.pkl"))
joblib.dump(FEATURES,                    os.path.join(ML_DIR, "feature_names.pkl"))
joblib.dump(best_name,                   os.path.join(ML_DIR, "best_model_name.pkl"))

print("Saved: purchase_model.pkl, scaler.pkl, feature_names.pkl ✓")

# ─────────────────────────────────────────────
#  STEP 8 – CUSTOMER SEGMENTATION (K-Means)
# ─────────────────────────────────────────────
print("\n" + "=" * 60)
print("STEP 8 – CUSTOMER SEGMENTATION (K-Means)")
print("=" * 60)

# Compute purchase_frequency
orders = pd.read_csv(os.path.join(DATA_DIR, "orders_clean.csv"))
freq   = orders.groupby("customer_id").size().reset_index(name="purchase_frequency")
seg_df = customers.merge(freq, on="customer_id", how="left").fillna(0)

SEG_FEATURES = ["total_purchases","total_spending","average_order_value",
                "website_visits","purchase_frequency"]

X_seg = seg_df[SEG_FEATURES].fillna(0)
scaler_seg = StandardScaler()
X_seg_sc   = scaler_seg.fit_transform(X_seg)

# Elbow method
inertias = []
K_range  = range(2, 11)
for k in K_range:
    km = KMeans(n_clusters=k, random_state=42, n_init=10)
    km.fit(X_seg_sc)
    inertias.append(km.inertia_)

fig, ax = plt.subplots(figsize=(8, 5))
ax.plot(K_range, inertias, "bo-")
ax.set_title("Elbow Method – Optimal K"); ax.set_xlabel("K"); ax.set_ylabel("Inertia")
plt.tight_layout(); fig.savefig(os.path.join(PLOTS_DIR, "13_elbow_method.png")); plt.close()
print("Elbow chart saved ✓")

# Fit with K=4
k_final   = 4
kmeans    = KMeans(n_clusters=k_final, random_state=42, n_init=10)
seg_df["cluster"] = kmeans.fit_predict(X_seg_sc)

# Label clusters by average total_spending
cluster_means = seg_df.groupby("cluster")["total_spending"].mean().sort_values(ascending=False)
labels_map = {
    cluster_means.index[0]: "Premium Customer",
    cluster_means.index[1]: "Regular Customer",
    cluster_means.index[2]: "Occasional Customer",
    cluster_means.index[3]: "At-Risk Customer",
}
seg_df["segment"] = seg_df["cluster"].map(labels_map)

print("\nCluster summary:")
print(seg_df.groupby("segment")[SEG_FEATURES].mean().round(2))

# Visualise
fig, ax = plt.subplots(figsize=(9, 6))
for seg, grp in seg_df.groupby("segment"):
    ax.scatter(grp["total_spending"], grp["total_purchases"], label=seg, alpha=0.7)
ax.set_title("Customer Segments"); ax.set_xlabel("Total Spending"); ax.set_ylabel("Total Purchases")
ax.legend(); plt.tight_layout(); fig.savefig(os.path.join(PLOTS_DIR, "14_customer_segments.png")); plt.close()

# Save segmentation model + metadata
joblib.dump(kmeans,                       os.path.join(ML_DIR, "segmentation_model.pkl"))
joblib.dump(scaler_seg,                   os.path.join(ML_DIR, "scaler_seg.pkl"))
joblib.dump(SEG_FEATURES,                 os.path.join(ML_DIR, "seg_features.pkl"))
joblib.dump(labels_map,                   os.path.join(ML_DIR, "cluster_labels.pkl"))

# Save updated customers with segments
seg_df[["customer_id","segment"]].to_csv(
    os.path.join(DATA_DIR, "customer_segments.csv"), index=False)

print("\nSaved: segmentation_model.pkl, scaler_seg.pkl, cluster_labels.pkl ✓")
print("\n✓ All ML models trained and saved")
