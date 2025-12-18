# main.py
"""
FastAPI应用主入口
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from config.settings import settings
from config.database import init_db
import os

# 创建FastAPI应用
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="机加工精密零件智能报价系统",
    debug=settings.DEBUG
)

# 配置CORS - 安全修复：限制允许的方法和头
allowed_origins = os.getenv('ALLOWED_ORIGINS', 'https://jzchardware.cn,http://localhost:3000,http://localhost:6001').split(',')
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    # 安全修复：仅允许必要的 HTTP 方法
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    # 安全修复：仅允许必要的请求头
    allow_headers=["Content-Type", "Authorization", "Accept", "Origin", "X-Requested-With"],
)

# 挂载静态文件目录
if os.path.exists(settings.UPLOAD_DIR):
    app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

# 导入路由
from api import drawings, materials, processes, products, quotes, ocr_corrections, boms, integration, auth
from api import routes as process_routes  # 工艺路线管理（避免与fastapi.routing冲突）
app.include_router(auth.router, prefix="/api/auth", tags=["认证"])
app.include_router(drawings.router, prefix="/api/drawings", tags=["图纸管理"])
app.include_router(materials.router, prefix="/api/materials", tags=["材料库"])
app.include_router(processes.router, prefix="/api/processes", tags=["工艺库"])
app.include_router(products.router, prefix="/api/products", tags=["产品管理"])
app.include_router(quotes.router, prefix="/api/quotes", tags=["报价管理"])
app.include_router(ocr_corrections.router, prefix="/api/ocr", tags=["OCR学习"])
app.include_router(boms.router, prefix="/api", tags=["BOM管理"])
app.include_router(process_routes.router, prefix="/api", tags=["工艺路线管理"])
app.include_router(integration.router, prefix="/api/integration", tags=["跨系统集成"])


@app.on_event("startup")
async def startup_event():
    """启动时初始化"""
    # 尝试使用统一日志配置
    try:
        import sys
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'shared'))
        from logging_config import get_system_logger
        logger = get_system_logger('quote')
        logger.info(f"启动 {settings.APP_NAME} v{settings.APP_VERSION}")
    except ImportError:
        print(f"🚀 启动 {settings.APP_NAME} v{settings.APP_VERSION}")

    init_db()

    # Initialize authentication database
    try:
        import sys
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
        from shared.auth import init_auth_db
        init_auth_db()
        print("✅ 认证数据库初始化成功")
    except Exception as e:
        print(f"⚠️ 认证数据库初始化失败: {e}")

    try:
        logger.info("数据库连接成功")
    except:
        print("✅ 数据库连接成功")


@app.get("/")
async def root():
    """根路径"""
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "message": "欢迎使用机加工报价系统"
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.getenv('PORT', 8001))  # 使用环境变量PORT，默认8001
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=settings.DEBUG
    )
