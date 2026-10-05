"""Admin APIs — no auth required."""
from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.models import Order, OrderItem, Product, Customer

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/sales-summary")
def sales_summary(db: Session = Depends(get_db)):
    total_revenue   = db.query(func.sum(Order.total_amount)).scalar() or 0.0
    total_orders    = db.query(func.count(Order.order_id)).scalar() or 0
    total_customers = db.query(func.count(Customer.customer_id)).scalar() or 0
    avg_order       = round(total_revenue / total_orders, 2) if total_orders else 0.0
    return {"total_revenue": round(total_revenue, 2), "total_orders": total_orders,
            "total_customers": total_customers, "avg_order_value": avg_order}


@router.get("/top-products")
def top_products(limit: int = 10, db: Session = Depends(get_db)):
    rows = (db.query(Product.product_id, Product.product_name, Product.category,
                     func.sum(OrderItem.quantity).label("units_sold"),
                     func.sum(OrderItem.price).label("revenue"))
            .join(OrderItem, Product.product_id == OrderItem.product_id)
            .group_by(Product.product_id)
            .order_by(func.sum(OrderItem.price).desc()).limit(limit).all())
    return [{"product_id": r.product_id, "product_name": r.product_name,
             "category": r.category, "units_sold": int(r.units_sold),
             "revenue": round(float(r.revenue), 2)} for r in rows]


@router.get("/top-customers")
def top_customers(limit: int = 10, db: Session = Depends(get_db)):
    rows = db.query(Customer).order_by(Customer.total_spending.desc()).limit(limit).all()
    return [{"customer_id": c.customer_id, "name": c.name, "city": c.city,
             "total_spending": round(c.total_spending, 2),
             "total_purchases": c.total_purchases, "segment": c.segment} for c in rows]


@router.get("/category-sales")
def category_sales(db: Session = Depends(get_db)):
    rows = (db.query(Product.category,
                     func.sum(OrderItem.price).label("revenue"),
                     func.count(OrderItem.id).label("orders"))
            .join(OrderItem, Product.product_id == OrderItem.product_id)
            .group_by(Product.category)
            .order_by(func.sum(OrderItem.price).desc()).all())
    return [{"category": r.category, "revenue": round(float(r.revenue), 2),
             "orders": int(r.orders)} for r in rows]


@router.get("/customer-segments")
def customer_segments(db: Session = Depends(get_db)):
    rows = (db.query(Customer.segment, func.count(Customer.customer_id).label("count"))
            .group_by(Customer.segment).all())
    return [{"segment": r.segment or "Unknown", "count": r.count} for r in rows]


@router.get("/low-stock-products")
def low_stock(threshold: int = 20, db: Session = Depends(get_db)):
    products = db.query(Product).filter(Product.stock <= threshold).order_by(Product.stock.asc()).all()
    return [{"product_id": p.product_id, "product_name": p.product_name,
             "category": p.category, "stock": p.stock, "price": p.price} for p in products]
