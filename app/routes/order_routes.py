from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.models import Order, OrderItem, Product, Customer, CustomerActivity, Cart
from app.schemas import OrderCreate, OrderResponse

router = APIRouter(prefix="/orders", tags=["Orders"])


def _update_customer_stats(customer_id: int, amount: float, db: Session):
    cust = db.query(Customer).filter(Customer.customer_id == customer_id).first()
    if cust:
        cust.total_purchases    += 1
        cust.total_spending     += amount
        cust.average_order_value = cust.total_spending / cust.total_purchases


def _update_activity(customer_id: int, product_id: int, qty: int, db: Session):
    act = db.query(CustomerActivity).filter(
        CustomerActivity.customer_id == customer_id,
        CustomerActivity.product_id  == product_id,
    ).first()
    if act:
        act.purchased          += 1
        act.previous_purchases += qty
        act.cart_additions     += 1
    else:
        db.add(CustomerActivity(
            customer_id        = customer_id,
            product_id         = product_id,
            previous_purchases = qty,
            purchased          = 1,
            cart_additions     = 1,
        ))


@router.post("", response_model=OrderResponse, status_code=201)
def place_order(data: OrderCreate, db: Session = Depends(get_db)):
    if not db.query(Customer).filter(Customer.customer_id == data.customer_id).first():
        raise HTTPException(status_code=404, detail="Customer not found")
    if not data.items:
        raise HTTPException(status_code=400, detail="Order must contain at least one item")

    total = 0.0
    order_items = []
    for it in data.items:
        prod = db.query(Product).filter(Product.product_id == it.product_id).first()
        if not prod:
            raise HTTPException(status_code=404, detail=f"Product {it.product_id} not found")
        if prod.stock < it.quantity:
            raise HTTPException(status_code=400,
                                detail=f"Insufficient stock for {prod.product_name}. Available: {prod.stock}")
        discounted = prod.price * (1 - prod.discount / 100)
        item_total = round(discounted * it.quantity, 2)
        total     += item_total
        prod.stock -= it.quantity
        order_items.append(OrderItem(product_id=it.product_id, quantity=it.quantity, price=item_total))

    order = Order(
        customer_id    = data.customer_id,
        total_amount   = round(total, 2),
        payment_method = data.payment_method,
        shipping_address = data.shipping_address,
    )
    db.add(order); db.flush()

    for oi in order_items:
        oi.order_id = order.order_id
        db.add(oi)

    _update_customer_stats(data.customer_id, total, db)
    for it in data.items:
        _update_activity(data.customer_id, it.product_id, it.quantity, db)

    db.query(Cart).filter(Cart.customer_id == data.customer_id).delete()
    db.commit(); db.refresh(order)
    return order


@router.get("", response_model=List[OrderResponse])
def list_orders(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    return db.query(Order).offset(skip).limit(limit).all()


@router.get("/{order_id}", response_model=OrderResponse)
def get_order(order_id: int, db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.order_id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@router.get("/customer/{customer_id}", response_model=List[OrderResponse], tags=["Customers"])
def get_customer_orders(customer_id: int, db: Session = Depends(get_db)):
    if not db.query(Customer).filter(Customer.customer_id == customer_id).first():
        raise HTTPException(status_code=404, detail="Customer not found")
    return db.query(Order).filter(Order.customer_id == customer_id).order_by(Order.order_date.desc()).all()
