# 投资大师 — 部署指南

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端 | Python 3.11 + FastAPI + uvicorn |
| 前端 | React 18 + Vite（构建为静态文件，由后端直接托管） |
| 数据库 | SQLite（文件路径：`data/touzidashi.db`） |
| 文件上传 | 存储于 `data/uploads/` |
| LLM | Anthropic Claude（通过 API Key 调用，支持自定义接入地址） |

生产环境只需运行 **一个服务**（FastAPI），它同时托管 API 和前端页面。

---

## 推荐部署方式：Railway

Railway 支持 Docker 构建，有持久化磁盘，适合这个项目。

### 前提条件

- Railway 账号：https://railway.app
- 代码已推送到 GitHub 私有仓库

### 步骤

#### 1. 创建 Railway 项目

1. 登录 Railway → New Project → Deploy from GitHub repo
2. 选择 `touzidashi` 仓库，Railway 会自动检测 `Dockerfile` 并开始构建

#### 2. 挂载持久化磁盘

> **重要**：不挂载磁盘的话，每次重新部署数据库和上传文件都会丢失。

1. 进入服务页面 → **Volumes** → Add Volume
2. Mount Path 填写：`/app/data`
3. 推荐容量：10 GB（视实际使用调整）

#### 3. 配置环境变量

进入服务页面 → **Variables**，逐一添加以下变量：

```
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=<实际 Key>
ANTHROPIC_MODEL=claude-opus-4-8
ANTHROPIC_BASE_URL=<接入地址，如使用中转则填中转 URL>
DEBUG=false
PORT=8000
DATABASE_URL=sqlite+aiosqlite:////app/data/touzidashi.db
UPLOAD_DIR=/app/data/uploads
```

> `DATABASE_URL` 和 `UPLOAD_DIR` 使用绝对路径（`/app/data/...`），与 Volume 挂载点对应。

#### 4. 触发部署

环境变量保存后 Railway 会自动重新部署。构建过程约 3-5 分钟（包含前端 npm build）。

#### 5. 验证

部署成功后，访问 Railway 分配的域名（如 `https://touzidashi-xxx.up.railway.app`）：

- 首页正常加载 → 前端 OK
- 访问 `/health` 返回 `{"status":"ok"}` → 后端 OK
- 上传一个 PDF 走完评估流程 → 全链路 OK

---

## 自定义域名（可选）

Railway 服务页 → Settings → Domains → Add Custom Domain，填入你自己的域名并按提示配置 CNAME。

---

## 本地开发

```bash
# 后端
cd touzidashi
cp .env.example .env   # 填入真实 API Key
pip install -r requirements.txt
python run.py          # 启动在 :8000

# 前端（另开终端）
cd touzidashi/client
npm install
npm run dev            # 启动在 :5173，API 请求自动代理到 :8000
```

---

## 注意事项

- `.env` 文件含 API Key，**不要提交到 Git**（已在 `.gitignore` 中排除）
- 如更换 LLM 接入地址或 Key，在 Railway Variables 修改后重新部署即可
- SQLite 适合小团队使用；如需多并发写入或更高可靠性，可迁移到 PostgreSQL（需改 `DATABASE_URL` 和相关依赖）
