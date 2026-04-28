from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api.router import api_router
from app.core.database import engine
from app.core.exception_handlers import register_exception_handlers
#FastAPI 新版的生命周期管理
#项目启动时先检查数据库能不能连上，项目关闭时自动清理资源
@asynccontextmanager
async def lifespan(_: FastAPI):
    #启动时执行：尝试连接数据库
    async with engine.begin() as conn:
        await conn.execute(text("SELECT 1"))
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
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)

@app.get("/")
async def root() -> dict[str, str]:
    return {"message": "Xiaobaicai Space API is running"}

@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "OK"}