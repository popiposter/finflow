"""API v1 router."""

from fastapi import APIRouter

from app.api.v1 import auth, health, planned_payments, transactions

router = APIRouter(prefix="/api/v1")

router.include_router(health.router)
router.include_router(auth.router)
router.include_router(transactions.router)
router.include_router(planned_payments.router)
