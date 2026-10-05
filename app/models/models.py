from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Boolean,
    ForeignKey, Text, Enum as SAEnum
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import enum


class UserRole(str, enum.Enum):
    customer = "customer"
    admin = "admin"


class OrderStatus(str, enum.Enum):
    pending = "pending"
    confirmed = "confirmed"
    shipped = "shipped"
    delivered = "delivered"
    cancelled = "cancelled"


class PaymentMethod(str, enum.Enum):
    credit_card = "credit_card"
    debit_card = "debit_card"
    paypal = "paypal"
    upi = "upi"
    cash_on_delivery = "cash_on_delivery"


# ─────────────────────────────────────────────
#  USER / CUSTOMER
# ─────────────────────────────────────────────
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(SAEnum(UserRole), default=UserRole.customer)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())

    customer = relationship("Customer", back_populates="user", uselist=False)


class Customer(Base):
    __tablename__ = "customers"

    customer_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=True)
    name = Column(String(150), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    age = Column(Integer, nullable=False)
    gender = Column(String(10))
    city = Column(String(100))
    phone = Column(String(20))
    registration_date = Column(DateTime, server_default=func.now())
    total_purchases = Column(Integer, default=0)
    total_spending = Column(Float, default=0.0)
    average_order_value = Column(Float, default=0.0)
    website_visits = Column(Integer, default=0)
    segment = Column(String(50), default="New Customer")

    user = relationship("User", back_populates="customer")
    orders = relationship("Order", back_populates="customer")
    cart_items = relationship("Cart", back_populates="customer")
    wishlist_items = relationship("Wishlist", back_populates="customer")
    activities = relationship("CustomerActivity", back_populates="customer")


# ─────────────────────────────────────────────
#  PRODUCT
# ─────────────────────────────────────────────
class Product(Base):
    __tablename__ = "products"

    product_id = Column(Integer, primary_key=True, index=True)
    product_name = Column(String(255), nullable=False)
    category = Column(String(100), nullable=False)
    price = Column(Float, nullable=False)
    rating = Column(Float, default=0.0)
    stock = Column(Integer, default=0)
    discount = Column(Float, default=0.0)
    description = Column(Text, nullable=True)
    image_url = Column(String(500), nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    order_items = relationship("OrderItem", back_populates="product")
    cart_items = relationship("Cart", back_populates="product")
    wishlist_items = relationship("Wishlist", back_populates="product")
    activities = relationship("CustomerActivity", back_populates="product")


# ─────────────────────────────────────────────
#  ORDER
# ─────────────────────────────────────────────
class Order(Base):
    __tablename__ = "orders"

    order_id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.customer_id"), nullable=False)
    order_date = Column(DateTime, server_default=func.now())
    total_amount = Column(Float, nullable=False)
    payment_method = Column(SAEnum(PaymentMethod), default=PaymentMethod.cash_on_delivery)
    order_status = Column(SAEnum(OrderStatus), default=OrderStatus.pending)
    shipping_address = Column(Text, nullable=True)

    customer = relationship("Customer", back_populates="orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.order_id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.product_id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)

    order = relationship("Order", back_populates="items")
    product = relationship("Product", back_populates="order_items")


# ─────────────────────────────────────────────
#  CART
# ─────────────────────────────────────────────
class Cart(Base):
    __tablename__ = "cart"

    cart_id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.customer_id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.product_id"), nullable=False)
    quantity = Column(Integer, default=1)
    added_at = Column(DateTime, server_default=func.now())

    customer = relationship("Customer", back_populates="cart_items")
    product = relationship("Product", back_populates="cart_items")


# ─────────────────────────────────────────────
#  WISHLIST
# ─────────────────────────────────────────────
class Wishlist(Base):
    __tablename__ = "wishlist"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.customer_id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.product_id"), nullable=False)
    added_at = Column(DateTime, server_default=func.now())

    customer = relationship("Customer", back_populates="wishlist_items")
    product = relationship("Product", back_populates="wishlist_items")


# ─────────────────────────────────────────────
#  CUSTOMER ACTIVITY
# ─────────────────────────────────────────────
class CustomerActivity(Base):
    __tablename__ = "customer_activity"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.customer_id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.product_id"), nullable=False)
    product_views = Column(Integer, default=0)
    cart_additions = Column(Integer, default=0)
    wishlist_additions = Column(Integer, default=0)
    previous_purchases = Column(Integer, default=0)
    time_spent = Column(Float, default=0.0)  # minutes
    purchased = Column(Integer, default=0)   # 0 or 1
    last_updated = Column(DateTime, server_default=func.now(), onupdate=func.now())

    customer = relationship("Customer", back_populates="activities")
    product = relationship("Product", back_populates="activities")
