from fastapi import APIRouter

from app.routers.evaluation import router as evaluation_router
from app.routers.config import router as config_router

router = APIRouter()
router.include_router(evaluation_router)
router.include_router(config_router)
