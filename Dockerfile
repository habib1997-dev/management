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

# Flatten the backend tree so CWD == package root: alembic.ini, alembic/,
# src/ and scripts/ all live directly under /app/backend (this is the layout
# the app, alembic.ini and `python -m scripts.*` command expect).
WORKDIR /app/backend
ENV PYTHONPATH=/app/backend/src
ENV FRONTEND_DIST=/app/frontend/dist

COPY backend/pyproject.toml backend/alembic.ini ./
COPY backend/alembic/ ./alembic/
COPY backend/src/ ./src/
COPY backend/scripts/ ./scripts/

RUN pip install --no-cache-dir .

COPY --from=frontend /app/frontend/dist /app/frontend/dist

EXPOSE 8000
# Prod startup: apply migrations only, then serve. Never seed/demo here —
# the first admin is created once via scripts.create_admin.
CMD ["sh", "-c", "cd /app/backend && alembic upgrade head && uvicorn student_management.main:app --host 0.0.0.0 --port ${PORT:-8000}"]