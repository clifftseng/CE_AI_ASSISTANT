# ---- Stage 1: build frontend ----
FROM node:20-slim AS fe-build
WORKDIR /fe
COPY frontend/package*.json /fe/
RUN npm install
COPY frontend /fe
RUN npm run build   # 產出 /fe/dist

# ---- Stage 2: backend ----
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# 複製後端程式碼
COPY backend /app

# 複製前端建置產物到 /app/static
COPY --from=fe-build /fe/dist /app/static

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]