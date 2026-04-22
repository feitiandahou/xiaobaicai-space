from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from .config import settings

#创建异步引擎 echo=True用于打印SQL语句
engine = create_async_engine(settings.DATABASE_URL, echo=True)

#创建异步会话工厂
AsyncSessionLocal = sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False
)

#创建基类， 所有模型都要继承它
Base = declarative_base()

#依赖注入：获取数据库会话
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session