"""
ML API endpoints — no auth required.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.models import Customer, Product, CustomerActivity, Order
from app.schemas import (
    PredictionRequest, PredictionResponse,
    RecommendationResponse, RecommendedProduct,
    SegmentResponse, DashboardResponse,
)

import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from ml.predictor   import predict_purchase, predict_segment, models_loaded
from ml.recommender import get_recommendations

router = APIRouter(tags=["Machine Learning"])


def _cust_or_404(customer_id: int, db: Session) -> Customer:
    c = db.query(Customer).filter(Customer.customer_id == customer_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Customer not found")
    return c


def _prod_or_404(product_id: int, db: Session) -> Product:
    p = db.query(Product).filter(Product.product_id == product_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Product not found")
    return p


# ── Purchase Prediction ───────────────────────────────────────────────────────
@router.post("/predict-purchase", response_model=PredictionResponse)
def predict_purchase_api(req: PredictionRequest, db: Session = Depends(get_db)):
    if not models_loaded():
        raise HTTPException(status_code=503, detail="ML models not loaded. Run ml/train_models.py first.")
    cust = _cust_or_404(req.customer_id, db)
    prod = _prod_or_404(req.product_id,  db)
    act  = db.query(CustomerActivity).filter(
        CustomerActivity.customer_id == req.customer_id,
        CustomerActivity.product_id  == req.product_id,
    ).first()
    features = {
        "age"                : cust.age or 30,
        "total_purchases"    : cust.total_purchases,
        "total_spending"     : cust.total_spending,
        "average_order_value": cust.average_order_value,
        "website_visits"     : cust.website_visits,
        "product_price"      : prod.price,
        "product_rating"     : prod.rating,
        "product_views"      : act.product_views      if act else 0,
        "cart_additions"     : act.cart_additions      if act else 0,
        "wishlist_additions" : act.wishlist_additions  if act else 0,
        "previous_purchases" : act.previous_purchases  if act else 0,
        "time_spent"         : act.time_spent          if act else 0.0,
    }
    result = predict_purchase(features)
    return PredictionResponse(
        customer_id          = req.customer_id,
        product_id           = req.product_id,
        purchase_probability = result["probability"],
        prediction           = result["prediction"],
    )


# ── Recommendations ───────────────────────────────────────────────────────────
@router.get("/recommendations/{customer_id}", response_model=RecommendationResponse)
def get_recs(customer_id: int, top_n: int = 5, db: Session = Depends(get_db)):
    _cust_or_404(customer_id, db)
    recs = get_recommendations(customer_id, top_n)
    return RecommendationResponse(
        customer_id     = customer_id,
        recommendations = [
            RecommendedProduct(
                product_id   = r["product_id"],
                product_name = r["product_name"],
                category     = r.get("category"),
                price        = r.get("price"),
                rating       = r.get("rating"),
                score        = round(r["score"], 4),
            ) for r in recs
        ],
    )


# ── Customer Segment ──────────────────────────────────────────────────────────
@router.get("/customer-segment/{customer_id}", response_model=SegmentResponse)
def get_segment(customer_id: int, db: Session = Depends(get_db)):
    if not models_loaded():
        raise HTTPException(status_code=503, detail="ML models not available")
    cust        = _cust_or_404(customer_id, db)
    order_count = db.query(Order).filter(Order.customer_id == customer_id).count()
    segment     = predict_segment({
        "total_purchases"    : cust.total_purchases,
        "total_spending"     : cust.total_spending,
        "average_order_value": cust.average_order_value,
        "website_visits"     : cust.website_visits,
        "purchase_frequency" : order_count,
    })
    cust.segment = segment
    db.commit()
    return SegmentResponse(customer_id=customer_id, segment=segment)


# ── Dashboard ─────────────────────────────────────────────────────────────────
@router.get("/customer-dashboard/{customer_id}", response_model=DashboardResponse)
def get_dashboard(customer_id: int, db: Session = Depends(get_db)):
    cust = _cust_or_404(customer_id, db)
    orders = (db.query(Order)
              .filter(Order.customer_id == customer_id)
              .order_by(Order.order_date.desc()).limit(5).all())
    prev = [{"order_id": o.order_id, "order_date": str(o.order_date),
             "total_amount": o.total_amount, "status": o.order_status} for o in orders]
    order_count = db.query(Order).filter(Order.customer_id == customer_id).count()

    segment = cust.segment or "New Customer"
    if models_loaded():
        segment = predict_segment({
            "total_purchases"    : cust.total_purchases,
            "total_spending"     : cust.total_spending,
            "average_order_value": cust.average_order_value,
            "website_visits"     : cust.website_visits,
            "purchase_frequency" : order_count,
        })
        cust.segment = segment
        db.commit()

    recs = get_recommendations(customer_id, top_n=5)
    recs_out = [RecommendedProduct(
        product_id=r["product_id"], product_name=r["product_name"],
        category=r.get("category"), price=r.get("price"),
        rating=r.get("rating"), score=round(r["score"], 4),
    ) for r in recs]

    predictions = []
    if models_loaded():
        for r in recs[:3]:
            prod = db.query(Product).filter(Product.product_id == r["product_id"]).first()
            if prod:
                act = db.query(CustomerActivity).filter(
                    CustomerActivity.customer_id == customer_id,
                    CustomerActivity.product_id  == prod.product_id,
                ).first()
                res = predict_purchase({
                    "age": cust.age or 30,
                    "total_purchases": cust.total_purchases,
                    "total_spending": cust.total_spending,
                    "average_order_value": cust.average_order_value,
                    "website_visits": cust.website_visits,
                    "product_price": prod.price,
                    "product_rating": prod.rating,
                    "product_views": act.product_views if act else 0,
                    "cart_additions": act.cart_additions if act else 0,
                    "wishlist_additions": act.wishlist_additions if act else 0,
                    "previous_purchases": act.previous_purchases if act else 0,
                    "time_spent": act.time_spent if act else 0.0,
                })
                predictions.append({
                    "product_id": prod.product_id, "product_name": prod.product_name,
                    "probability": res["probability"], "prediction": res["prediction"],
                })

    return DashboardResponse(
        customer_id=customer_id, name=cust.name, email=cust.email,
        total_orders=order_count, total_spending=cust.total_spending,
        average_order_value=cust.average_order_value,
        previous_purchases=prev, segment=segment,
        recommendations=recs_out, purchase_predictions=predictions,
    )
