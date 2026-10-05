from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.models import Product
from app.schemas import ProductCreate, ProductUpdate, ProductResponse

router = APIRouter(prefix="/products", tags=["Products"])


@router.post("", response_model=ProductResponse, status_code=201)
def create_product(data: ProductCreate, db: Session = Depends(get_db)):
    prod = Product(**data.model_dump())
    db.add(prod); db.commit(); db.refresh(prod)
    return prod


@router.get("", response_model=List[ProductResponse])
def list_products(
    skip    : int            = 0,
    limit   : int            = 60,
    category: Optional[str] = Query(default=None),
    search  : Optional[str] = Query(default=None),
    db      : Session        = Depends(get_db),
):
    q = db.query(Product)
    if category:
        q = q.filter(Product.category.ilike(f"%{category}%"))
    if search:
        q = q.filter(Product.product_name.ilike(f"%{search}%"))
    return q.offset(skip).limit(limit).all()


@router.get("/{product_id}", response_model=ProductResponse)
def get_product(product_id: int, db: Session = Depends(get_db)):
    prod = db.query(Product).filter(Product.product_id == product_id).first()
    if not prod:
        raise HTTPException(status_code=404, detail="Product not found")
    return prod


@router.put("/{product_id}", response_model=ProductResponse)
def update_product(product_id: int, data: ProductUpdate, db: Session = Depends(get_db)):
    prod = db.query(Product).filter(Product.product_id == product_id).first()
    if not prod:
        raise HTTPException(status_code=404, detail="Product not found")
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(prod, field, value)
    db.commit(); db.refresh(prod)
    return prod


@router.delete("/{product_id}", status_code=204)
def delete_product(product_id: int, db: Session = Depends(get_db)):
    prod = db.query(Product).filter(Product.product_id == product_id).first()
    if not prod:
        raise HTTPException(status_code=404, detail="Product not found")
    db.delete(prod); db.commit()
