# --- Stage 1: build the React frontend ---
FROM node:20-alpine AS frontend
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci --ignore-scripts
COPY frontend/ ./
RUN npm run build

# --- Stage 2: production Python image ---
FROM python:3.11-slim
RUN apt-get update && apt-get install -y --no-install-recommends libpq-dev && rm -rf /var/lib/apt/lists/*

WORKDIR /app/backend
ENV PYTHONPATH=/app/backend/src

COPY backend/pyproject.toml backend/alembic.ini backend/alembic/ ./backend/
COPY backend/src/ ./backend/src/
COPY backend/scripts/ ./backend/scripts/

RUN pip install --no-cache-dir ./backend

COPY --from=frontend /app/frontend/dist /app/frontend/dist

EXPOSE 8000
CMD ["sh", "-c", "cd /app/backend && alembic upgrade head && python -m scripts.seed && uvicorn student_management.main:app --host 0.0.0.0 --port $PORT"]
