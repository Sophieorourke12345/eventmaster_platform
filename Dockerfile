FROM node:22-alpine AS frontend-build
WORKDIR /build/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.12-slim AS production
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_ENV=production
WORKDIR /app
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt
COPY backend/ /app/backend/
COPY --from=frontend-build /build/frontend/dist /app/frontend/dist
WORKDIR /app/backend
CMD ["sh", "-c", "flask --app run.py db upgrade && gunicorn --bind 0.0.0.0:${PORT:-10000} --workers 2 --threads 4 --timeout 120 run:app"]
