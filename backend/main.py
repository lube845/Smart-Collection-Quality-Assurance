"""
ASR智能质检系统 - 主入口
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import time
from loguru import logger

from .core.config import settings
from .core.database import init_db
from .core.redis import redis_client
from .api import (
    auth_router, user_router, org_router,
    recording_router, rule_router,
    app_group_router, stats_router, export_router,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时
    logger.info("正在启动应用...")

    # 初始化数据库
    try:
        await init_db()
        logger.info("数据库初始化完成")
    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")

    # 初始化Redis连接池
    try:
        await redis_client.client.ping()
        logger.info("Redis连接成功")
    except Exception as e:
        logger.warning(f"Redis连接失败: {e}")

    yield

    # 关闭时
    logger.info("正在关闭应用...")
    await redis_client.close()


# 创建FastAPI应用
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="催收语音自动化转写与智能打分系统",
    lifespan=lifespan,
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应该限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 请求日志中间件
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time

    logger.info(
        f"{request.method} {request.url.path} - {response.status_code} - {process_time:.3f}s"
    )

    return response


# 错误处理
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"全局异常: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "服务器内部错误", "message": str(exc)},
    )


# 健康检查
@app.get("/health")
async def health_check():
    return {"status": "ok", "version": settings.APP_VERSION}


# 注册路由
app.include_router(auth_router, prefix="/api/v1")
app.include_router(user_router, prefix="/api/v1")
app.include_router(org_router, prefix="/api/v1")
app.include_router(recording_router, prefix="/api/v1")
app.include_router(rule_router, prefix="/api/v1")
app.include_router(app_group_router, prefix="/api/v1")
app.include_router(stats_router, prefix="/api/v1")
app.include_router(export_router, prefix="/api/v1")


# 根路径
@app.get("/")
async def root():
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
    )
