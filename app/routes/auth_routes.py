from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.models import User, Customer
from app.schemas import RegisterRequest, LoginRequest, Token
from app.auth import hash_password, verify_password, create_access_token

router = APIRouter(tags=["Authentication"])


@router.post("/register", response_model=dict, status_code=status.HTTP_201_CREATED)
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == req.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        email           = req.email,
        hashed_password = hash_password(req.password),
        role            = req.role,
    )
    db.add(user)
    db.flush()  # get user.id without committing

    # Auto-create a Customer profile for every new user
    if req.role == "customer":
        # Check if customer with this email already exists
        existing = db.query(Customer).filter(Customer.email == req.email).first()
        if not existing:
            name = req.email.split("@")[0].replace(".", " ").title()
            customer = Customer(
                user_id  = user.id,
                name     = name,
                email    = req.email,
                age      = 25,          # default – can be updated via PUT /customers
                segment  = "New Customer",
            )
            db.add(customer)

    db.commit()
    db.refresh(user)

    # Fetch the newly created customer_id (if any)
    cust = db.query(Customer).filter(Customer.email == req.email).first()

    return {
        "message"    : "Registration successful",
        "user_id"    : user.id,
        "customer_id": cust.customer_id if cust else None,
        "email"      : user.email,
        "role"       : user.role,
    }


@router.post("/login", response_model=dict)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == req.email).first()
    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token    = create_access_token({"sub": user.email, "role": user.role})
    customer = db.query(Customer).filter(Customer.email == req.email).first()

    return {
        "access_token": token,
        "token_type"  : "bearer",
        "customer_id" : customer.customer_id if customer else None,
        "role"        : user.role,
    }
