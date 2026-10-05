"""
SmartCart – Main FastAPI Application
Steps 11, 20, 21 – App wiring, error handling, CORS, static files.
"""

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.exc import IntegrityError
import os

from app.database import engine, Base
from app.routes import (
    auth_routes,
    customer_routes,
    product_routes,
    cart_routes,
    order_routes,
    ml_routes,
    admin_routes,
)

# Create all tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title       = "SmartCart – AI-Powered E-Commerce API",
    description = (
        "Complete e-commerce backend with JWT authentication, "
        "purchase prediction, customer segmentation, and product recommendations."
    ),
    version     = "1.0.0",
    docs_url    = "/docs",
    redoc_url   = "/redoc",
)

# ─── CORS ─────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins     = ["*"],
    allow_credentials = True,
    allow_methods     = ["*"],
    allow_headers     = ["*"],
)

# ─── Static files & templates ─────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
static_dir    = os.path.join(BASE_DIR, "static")
templates_dir = os.path.join(BASE_DIR, "templates")

if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

templates = Jinja2Templates(directory=templates_dir)


# ─── Global error handlers ────────────────────────────────────────────────────
@app.exception_handler(IntegrityError)
async def integrity_error_handler(request: Request, exc: IntegrityError):
    return JSONResponse(
        status_code = status.HTTP_400_BAD_REQUEST,
        content     = {"detail": "Database integrity error – possible duplicate entry"},
    )

@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    return JSONResponse(
        status_code = 404,
        content     = {"detail": "Resource not found"},
    )

@app.exception_handler(500)
async def server_error_handler(request: Request, exc):
    return JSONResponse(
        status_code = 500,
        content     = {"detail": "Internal server error"},
    )


# ─── Routers ──────────────────────────────────────────────────────────────────
app.include_router(auth_routes.router)
app.include_router(customer_routes.router)
app.include_router(product_routes.router)
app.include_router(cart_routes.router)
app.include_router(order_routes.router)
app.include_router(ml_routes.router)
app.include_router(admin_routes.router)


# ─── Frontend route ───────────────────────────────────────────────────────────
@app.get("/", include_in_schema=False)
async def serve_frontend(request: Request):
    index = os.path.join(templates_dir, "index.html")
    if os.path.exists(index):
        return templates.TemplateResponse("index.html", {"request": request})
    return JSONResponse({"message": "SmartCart API is running! Visit /docs"})


# ─── Health check ─────────────────────────────────────────────────────────────
@app.get("/health", tags=["System"])
def health_check():
    return {"status": "ok", "service": "SmartCart API"}
