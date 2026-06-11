# ── Stage 1: 构建 React 前端 ──
FROM node:20-slim AS frontend
WORKDIR /client
COPY client/package*.json ./
RUN npm install
COPY client/ ./
RUN npm run build

# ── Stage 2: Python 后端（最终镜像）──
FROM python:3.11-slim
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/
COPY run.py .

# 将前端构建产物复制进来
COPY --from=frontend /client/dist ./client/dist

# 创建数据目录（Railway 会用 Volume 覆盖 /app/data）
RUN mkdir -p data/uploads

EXPOSE 8000
CMD ["python", "run.py"]
