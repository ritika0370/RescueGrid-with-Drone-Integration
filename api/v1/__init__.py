"""
API v1 Router registry.
"""
from fastapi import APIRouter
from app.api.v1 import (
    ai,
    auth,
    departments,
    drones,
    final_reports,
    incidents,
    missions,
    reports,
    twilio_webhook,
    websockets,
)

api_v1_router = APIRouter()

api_v1_router.include_router(auth.router)
api_v1_router.include_router(reports.router)
api_v1_router.include_router(incidents.router)
api_v1_router.include_router(ai.router)
api_v1_router.include_router(departments.router)
api_v1_router.include_router(drones.router)
api_v1_router.include_router(missions.router)
api_v1_router.include_router(final_reports.router)
api_v1_router.include_router(twilio_webhook.router)
api_v1_router.include_router(websockets.router)
