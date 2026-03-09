"""API v1 router."""

from fastapi import APIRouter

from app.api.v1 import (
    accounts,
    auth,
    categories,
    health,
    planned_payments,
    projected_transactions,
    reports,
    transactions,
)

router = APIRouter(prefix="/api/v1")

router.include_router(health.router)
router.include_router(auth.router)
router.include_router(accounts.router)
router.include_router(categories.router)
router.include_router(transactions.router)
router.include_router(planned_payments.router)
router.include_router(projected_transactions.router)
router.include_router(reports.router)
