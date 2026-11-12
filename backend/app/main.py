from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.redis_client import close_redis, get_redis
from app.routers import auth as auth_router
from app.routers import admin as admin_router
from app.routers import admin_rates as admin_rates_router
from app.routers import company as company_router
from app.routers import deliverer as deliverer_router
from app.routers import webhooks as webhooks_router
from app.websocket import deliverer_ws, company_ws


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: warm up Redis connection
    await get_redis()
    yield
    # Shutdown: close Redis connection
    await close_redis()


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    debug=settings.debug,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(auth_router.router, prefix="/api/v1")
app.include_router(admin_router.router, prefix="/api/v1")
app.include_router(admin_rates_router.router, prefix="/api/v1")
app.include_router(company_router.router, prefix="/api/v1")
app.include_router(deliverer_router.router, prefix="/api/v1")
app.include_router(webhooks_router.router, prefix="/api/v1")
app.include_router(deliverer_ws.router)
app.include_router(company_ws.router)


@app.get("/health")
async def health_check():
    return {"status": "ok"}
