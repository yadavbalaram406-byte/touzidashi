import os
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.database import init_db
from app.config import get_settings
from app.routers import router

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    os.makedirs(settings.upload_dir, exist_ok=True)
    await init_db()
    yield


app = FastAPI(
    title="投资大师 - Investment Evaluator",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")


@app.get("/health")
async def health():
    return {"status": "ok", "app": "投资大师"}


# 托管前端静态文件（生产环境 Dockerfile 构建后存在）
_static_dir = Path("client/dist")
if _static_dir.exists():
    class SPAStaticFiles(StaticFiles):
        """SPA 深链接支持：真实文件正常返回，找不到的路径回退 index.html，
        交给前端路由（BrowserRouter）处理，避免 /detail/7、/result/7 直接 404。"""

        async def get_response(self, path, scope):
            try:
                return await super().get_response(path, scope)
            except StarletteHTTPException as ex:
                if ex.status_code == 404:
                    return await super().get_response("index.html", scope)
                raise

    app.mount("/", SPAStaticFiles(directory=str(_static_dir), html=True), name="static")
