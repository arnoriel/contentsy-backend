from fastapi import APIRouter

from app.api.routes import auth, upload, user

api_router = APIRouter(prefix="/api")
api_router.include_router(auth.router)
api_router.include_router(upload.router)
api_router.include_router(user.router)
