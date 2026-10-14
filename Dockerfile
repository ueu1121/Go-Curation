# Single-container production image: builds the React app and serves it from FastAPI (same origin).
# Status: documented, not yet verified (Docker is not available in the Emergent preview environment).
FROM node:20-bookworm-slim AS web
WORKDIR /web
COPY frontend/package.json frontend/yarn.lock ./
RUN yarn install --frozen-lockfile --ignore-scripts
COPY frontend/ ./
ENV REACT_APP_BACKEND_URL=""
RUN yarn build

FROM python:3.11-slim
WORKDIR /app/backend
COPY backend/requirements-app.txt ./
RUN pip install --no-cache-dir -r requirements-app.txt
COPY backend/ ./
COPY --from=web /web/build /app/static
ENV STATIC_DIR=/app/static APP_ENV=production DEMO_MODE=false
EXPOSE 8001
CMD ["sh", "-c", "uvicorn server:app --host 0.0.0.0 --port ${PORT:-8001}"]
