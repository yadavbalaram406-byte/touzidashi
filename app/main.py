import os
import html as _html
import re
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import init_db, get_db
from app.models.evaluation import Evaluation
from app.scoring import get_decision
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
_index_html = _static_dir / "index.html"
_icon_path = Path("icon.png")


def _inject_meta(html_text: str, *, title: str, desc: str, image: str, url: str) -> str:
    """把动态 og/twitter meta 注入到 index.html 的 <head>，供微信等爬虫读取。"""
    e = lambda s: _html.escape(s or "", quote=True)
    site_name = "from one origin · AI投资大师"
    icon_tags = ""
    if _icon_path.exists():
        # 移除构建产物里原有的 favicon，避免与自定义 icon 冲突（微信可能优先用排在前的）
        html_text = re.sub(r'<link[^>]*rel="(?:icon|apple-touch-icon)"[^>]*>', "", html_text, flags=re.I)
        icon_tags = (
            '<link rel="icon" href="/icon.png" />'
            '<link rel="apple-touch-icon" href="/icon.png" />'
        )
    tags = f"""<meta property="og:type" content="website" />
<meta property="og:title" content="{e(title)}" />
<meta property="og:description" content="{e(desc)}" />
<meta property="og:image" content="{e(image)}" />
<meta property="og:url" content="{e(url)}" />
<meta property="og:site_name" content="{e(site_name)}" />
<meta name="twitter:card" content="summary_large_image" />
<meta name="twitter:title" content="{e(title)}" />
<meta name="twitter:description" content="{e(desc)}" />
<meta name="twitter:image" content="{e(image)}" />
{icon_tags}"""
    # 替换已有 <title>，并在 </head> 前插入 og 标签
    html_text = re.sub(r"<title>.*?</title>", f"<title>{e(title)}</title>", html_text, count=1, flags=re.S)
    return html_text.replace("</head>", tags + "\n</head>", 1)


async def _render_share_page(evaluation_id: int, path_prefix: str, db: AsyncSession) -> HTMLResponse:
    """返回带动态 meta 的 index.html；记录不存在/未完成则返回原始壳交给前端处理。"""
    raw = _index_html.read_text(encoding="utf-8")
    ev = await db.get(Evaluation, evaluation_id)
    if ev and ev.status == "completed" and ev.final_score is not None:
        dec = get_decision(ev.final_score)
        score = int(round(ev.final_score))
        base = settings.site_base_url.rstrip("/")
        title = f"{ev.project_name} · {score}分"
        desc = f"{dec['icon']} 综合评分 {score}/100 ｜ {dec['label']}（{dec['chinese']}）"
        image = f"{base}/api/evaluations/{ev.id}/share-image"
        url = f"{base}{path_prefix}/{ev.id}"
        raw = _inject_meta(raw, title=title, desc=desc, image=image, url=url)
    return HTMLResponse(raw)


if _index_html.exists():
    @app.get("/icon.png", include_in_schema=False)
    async def favicon():
        return FileResponse(str(_icon_path)) if _icon_path.exists() else HTMLResponse(status_code=404)

    @app.get("/detail/{evaluation_id}", include_in_schema=False)
    async def detail_page(evaluation_id: int, db: AsyncSession = Depends(get_db)):
        return await _render_share_page(evaluation_id, "/detail", db)

    @app.get("/result/{evaluation_id}", include_in_schema=False)
    async def result_page(evaluation_id: int, db: AsyncSession = Depends(get_db)):
        return await _render_share_page(evaluation_id, "/result", db)


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
