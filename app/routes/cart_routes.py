from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.models import Cart, Customer, Product
from app.schemas import CartCreate, CartUpdate, CartResponse

router = APIRouter(prefix="/cart", tags=["Cart"])


@router.post("", response_model=CartResponse, status_code=201)
def add_to_cart(data: CartCreate, db: Session = Depends(get_db)):
    if not db.query(Customer).filter(Customer.customer_id == data.customer_id).first():
        raise HTTPException(status_code=404, detail="Customer not found")
    prod = db.query(Product).filter(Product.product_id == data.product_id).first()
    if not prod:
        raise HTTPException(status_code=404, detail="Product not found")
    if prod.stock < data.quantity:
        raise HTTPException(status_code=400, detail=f"Insufficient stock. Available: {prod.stock}")

    existing = db.query(Cart).filter(
        Cart.customer_id == data.customer_id,
        Cart.product_id  == data.product_id,
    ).first()
    if existing:
        existing.quantity = data.quantity
        db.commit(); db.refresh(existing)
        return existing

    item = Cart(**data.model_dump())
    db.add(item); db.commit(); db.refresh(item)
    return item


@router.get("/{customer_id}", response_model=List[CartResponse])
def get_cart(customer_id: int, db: Session = Depends(get_db)):
    if not db.query(Customer).filter(Customer.customer_id == customer_id).first():
        raise HTTPException(status_code=404, detail="Customer not found")
    items = db.query(Cart).filter(Cart.customer_id == customer_id).all()
    return items


@router.put("/{cart_id}", response_model=CartResponse)
def update_cart(cart_id: int, data: CartUpdate, db: Session = Depends(get_db)):
    item = db.query(Cart).filter(Cart.cart_id == cart_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Cart item not found")
    item.quantity = data.quantity
    db.commit(); db.refresh(item)
    return item


@router.delete("/{cart_id}", status_code=204)
def remove_from_cart(cart_id: int, db: Session = Depends(get_db)):
    item = db.query(Cart).filter(Cart.cart_id == cart_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Cart item not found")
    db.delete(item); db.commit()
