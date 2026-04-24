from contextlib import asynccontextmanager
from sqlalchemy import text
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.posts import router as post_router
from app.api.v1.users import router as user_router
from app.core.database import engine
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

app.include_router(post_router, prefix="/api/v1")
app.include_router(user_router, prefix="/api/v1")

@app.get("/")
async def root() -> dict[str, str]:
    return {"message": "Xiaobaicai Space API is running"}

@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "OK"}