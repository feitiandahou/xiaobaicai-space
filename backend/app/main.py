from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette import status
from sqlalchemy import text

from app.api.router import api_router
from app.core.config import settings
from app.core.database import engine
from app.core.exception_handlers import register_exception_handlers
from app.core.observability import RequestLoggingMiddleware, configure_logging, get_logger


configure_logging()
logger = get_logger(__name__)


async def check_database_readiness() -> None:
    async with engine.begin() as conn:
        await conn.execute(text("SELECT 1"))


#FastAPI 新版的生命周期管理
#项目启动时不把数据库可用性作为进程存活前提，readiness 负责对外暴露依赖状态
@asynccontextmanager
async def lifespan(_: FastAPI):
    try:
        await check_database_readiness()
        logger.info(
            "startup_readiness_check_passed",
            extra={
                "event": "startup_readiness_check_passed",
                "dependency": "database",
            },
        )
    except Exception:
        logger.warning(
            "startup_readiness_check_failed",
            extra={
                "event": "startup_readiness_check_failed",
                "dependency": "database",
            },
            exc_info=True,
        )
    yield

app = FastAPI(
    title="Xiaobaicai Space API",
    version="0.1.0",
    description="Backend API for the Xiaobaicai Space blog project.",
    lifespan=lifespan,
)

register_exception_handlers(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestLoggingMiddleware)

app.include_router(api_router)

@app.get("/")
async def root() -> dict[str, str]:
    return {"message": "Xiaobaicai Space API is running"}

@app.get("/health")
async def health() -> JSONResponse:
    return await health_ready()


@app.get("/health/live")
async def health_live() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/health/ready")
async def health_ready() -> JSONResponse:
    try:
        await check_database_readiness()
    except Exception:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "not_ready",
                "checks": {
                    "database": "unavailable",
                },
            },
        )

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "status": "ready",
            "checks": {
                "database": "ok",
            },
        },
    )