"""
ML inference helpers used by the FastAPI routes.
"""

import os
import joblib
import numpy as np
import pandas as pd

ML_DIR = os.path.dirname(__file__)

# Load artifacts once at import time
_purchase_model  = None
_scaler          = None
_feature_names   = None
_best_model_name = None
_seg_model       = None
_scaler_seg      = None
_seg_features    = None
_cluster_labels  = None


def _load_purchase():
    global _purchase_model, _scaler, _feature_names, _best_model_name
    if _purchase_model is None:
        _purchase_model  = joblib.load(os.path.join(ML_DIR, "purchase_model.pkl"))
        _scaler          = joblib.load(os.path.join(ML_DIR, "scaler.pkl"))
        _feature_names   = joblib.load(os.path.join(ML_DIR, "feature_names.pkl"))
        _best_model_name = joblib.load(os.path.join(ML_DIR, "best_model_name.pkl"))


def _load_segmentation():
    global _seg_model, _scaler_seg, _seg_features, _cluster_labels
    if _seg_model is None:
        _seg_model      = joblib.load(os.path.join(ML_DIR, "segmentation_model.pkl"))
        _scaler_seg     = joblib.load(os.path.join(ML_DIR, "scaler_seg.pkl"))
        _seg_features   = joblib.load(os.path.join(ML_DIR, "seg_features.pkl"))
        _cluster_labels = joblib.load(os.path.join(ML_DIR, "cluster_labels.pkl"))


def predict_purchase(features: dict) -> dict:
    """
    features: dict with keys matching feature_names
    Returns: {"probability": float, "prediction": str}
    """
    _load_purchase()
    row = pd.DataFrame([features])[_feature_names].fillna(0)

    if _best_model_name == "Logistic Regression":
        row_sc = _scaler.transform(row)
        prob   = float(_purchase_model.predict_proba(row_sc)[0][1])
    else:
        prob   = float(_purchase_model.predict_proba(row)[0][1])

    label = "Likely to Purchase" if prob >= 0.5 else "Unlikely to Purchase"
    return {"probability": round(prob, 4), "prediction": label}


def predict_segment(customer_features: dict) -> str:
    """
    customer_features: dict with keys matching seg_features
    Returns: segment label string
    """
    _load_segmentation()
    row     = pd.DataFrame([customer_features])[_seg_features].fillna(0)
    row_sc  = _scaler_seg.transform(row)
    cluster = int(_seg_model.predict(row_sc)[0])
    return _cluster_labels.get(cluster, "Regular Customer")


def models_loaded() -> bool:
    """Quick health-check for the API."""
    try:
        _load_purchase()
        _load_segmentation()
        return True
    except Exception:
        return False
