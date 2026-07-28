from fastapi import APIRouter
from app.api.health import router as health_router
from app.api.sessions import router as sessions_router
from app.api.analytics import router as analytics_router
from app.api.export import router as export_router
from app.api.predict import router as predict_router

api_router = APIRouter()

api_router.include_router(health_router)
api_router.include_router(sessions_router)
api_router.include_router(analytics_router)
api_router.include_router(export_router)
api_router.include_router(predict_router)
