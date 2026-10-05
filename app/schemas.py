"""
Step 18 – Pydantic Schemas with validation.
"""

from __future__ import annotations
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field, field_validator
from enum import Enum


# ─── Enums ────────────────────────────────────────────────────────────────────
class UserRole(str, Enum):
    customer = "customer"
    admin    = "admin"

class OrderStatus(str, Enum):
    pending   = "pending"
    confirmed = "confirmed"
    shipped   = "shipped"
    delivered = "delivered"
    cancelled = "cancelled"

class PaymentMethod(str, Enum):
    credit_card      = "credit_card"
    debit_card       = "debit_card"
    paypal           = "paypal"
    upi              = "upi"
    cash_on_delivery = "cash_on_delivery"


# ─── AUTH ─────────────────────────────────────────────────────────────────────
class RegisterRequest(BaseModel):
    email   : EmailStr
    password: str = Field(min_length=6, max_length=128)
    role    : UserRole = UserRole.customer

class LoginRequest(BaseModel):
    email   : EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type  : str = "bearer"

class TokenData(BaseModel):
    email: Optional[str] = None
    role : Optional[str] = None


# ─── CUSTOMER ─────────────────────────────────────────────────────────────────
class CustomerBase(BaseModel):
    name  : str = Field(min_length=2, max_length=150)
    email : EmailStr
    age   : int = Field(ge=18, le=100)
    gender: Optional[str] = Field(default=None, max_length=10)
    city  : Optional[str] = Field(default=None, max_length=100)
    phone : Optional[str] = Field(default=None, max_length=20)

class CustomerCreate(CustomerBase):
    pass

class CustomerUpdate(BaseModel):
    name  : Optional[str] = Field(default=None, min_length=2, max_length=150)
    age   : Optional[int] = Field(default=None, ge=18, le=100)
    gender: Optional[str] = None
    city  : Optional[str] = None
    phone : Optional[str] = None

class CustomerResponse(CustomerBase):
    customer_id         : int
    registration_date   : Optional[datetime] = None
    total_purchases     : int   = 0
    total_spending      : float = 0.0
    average_order_value : float = 0.0
    website_visits      : int   = 0
    segment             : str   = "New Customer"

    model_config = {"from_attributes": True}


# ─── PRODUCT ──────────────────────────────────────────────────────────────────
class ProductBase(BaseModel):
    product_name: str   = Field(min_length=2, max_length=255)
    category    : str   = Field(min_length=2, max_length=100)
    price       : float = Field(gt=0)
    rating      : float = Field(ge=0, le=5, default=0.0)
    stock       : int   = Field(ge=0, default=0)
    discount    : float = Field(ge=0, le=100, default=0.0)
    description : Optional[str] = None
    image_url   : Optional[str] = None

class ProductCreate(ProductBase):
    pass

class ProductUpdate(BaseModel):
    product_name: Optional[str]   = Field(default=None, min_length=2, max_length=255)
    category    : Optional[str]   = None
    price       : Optional[float] = Field(default=None, gt=0)
    rating      : Optional[float] = Field(default=None, ge=0, le=5)
    stock       : Optional[int]   = Field(default=None, ge=0)
    discount    : Optional[float] = Field(default=None, ge=0, le=100)
    description : Optional[str]  = None

class ProductResponse(ProductBase):
    product_id: int
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# ─── CART ─────────────────────────────────────────────────────────────────────
class CartCreate(BaseModel):
    customer_id: int = Field(gt=0)
    product_id : int = Field(gt=0)
    quantity   : int = Field(ge=1, le=100)

class CartUpdate(BaseModel):
    quantity: int = Field(ge=1, le=100)

class CartResponse(BaseModel):
    cart_id    : int
    customer_id: int
    product_id : int
    quantity   : int
    added_at   : Optional[datetime] = None
    product    : Optional[ProductResponse] = None

    model_config = {"from_attributes": True}


# ─── ORDER ────────────────────────────────────────────────────────────────────
class OrderItemCreate(BaseModel):
    product_id: int = Field(gt=0)
    quantity  : int = Field(ge=1)

    @field_validator("quantity")
    @classmethod
    def qty_positive(cls, v):
        if v < 1:
            raise ValueError("Quantity must be at least 1")
        return v

class OrderCreate(BaseModel):
    customer_id     : int = Field(gt=0)
    items           : List[OrderItemCreate]
    payment_method  : PaymentMethod = PaymentMethod.cash_on_delivery
    shipping_address: Optional[str] = None

class OrderItemResponse(BaseModel):
    id        : int
    product_id: int
    quantity  : int
    price     : float
    product   : Optional[ProductResponse] = None

    model_config = {"from_attributes": True}

class OrderResponse(BaseModel):
    order_id        : int
    customer_id     : int
    order_date      : Optional[datetime] = None
    total_amount    : float
    payment_method  : str
    order_status    : str
    shipping_address: Optional[str] = None
    items           : List[OrderItemResponse] = []

    model_config = {"from_attributes": True}


# ─── WISHLIST ─────────────────────────────────────────────────────────────────
class WishlistCreate(BaseModel):
    customer_id: int = Field(gt=0)
    product_id : int = Field(gt=0)

class WishlistResponse(BaseModel):
    id         : int
    customer_id: int
    product_id : int
    added_at   : Optional[datetime] = None
    product    : Optional[ProductResponse] = None

    model_config = {"from_attributes": True}


# ─── ML SCHEMAS ───────────────────────────────────────────────────────────────
class PredictionRequest(BaseModel):
    customer_id: int = Field(gt=0)
    product_id : int = Field(gt=0)

class PredictionResponse(BaseModel):
    customer_id          : int
    product_id           : int
    purchase_probability : float
    prediction           : str

class RecommendedProduct(BaseModel):
    product_id  : int
    product_name: str
    category    : Optional[str] = None
    price       : Optional[float] = None
    rating      : Optional[float] = None
    score       : float

class RecommendationResponse(BaseModel):
    customer_id    : int
    recommendations: List[RecommendedProduct]

class SegmentResponse(BaseModel):
    customer_id: int
    segment    : str

class DashboardResponse(BaseModel):
    customer_id        : int
    name               : str
    email              : str
    total_orders       : int
    total_spending      : float
    average_order_value : float
    previous_purchases  : List[dict] = []
    segment             : str
    recommendations     : List[RecommendedProduct] = []
    purchase_predictions: List[dict] = []
