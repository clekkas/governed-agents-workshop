# Multi-stage build: build the React UI, then run the Express backend that serves
# both the API and the built UI as static content. Single image, port 8080.

# ---- Stage 1: build the UI ----
FROM node:20-bookworm-slim AS ui-build
WORKDIR /ui
COPY app/readmission-review-tracker/package*.json ./
RUN npm ci
COPY app/readmission-review-tracker/ ./
RUN npm run build

# ---- Stage 2: backend runtime ----
FROM node:20-bookworm-slim AS runtime
ENV NODE_ENV=production
ENV HOST=0.0.0.0
ENV PORT=8080
WORKDIR /app/backend

# Install backend production deps only.
COPY backend/package*.json ./
RUN npm ci --omit=dev

# Backend source.
COPY backend/ ./

# Place the built UI where the backend resolver expects it:
# backend resolves ../../app/readmission-review-tracker/dist relative to src/.
COPY --from=ui-build /ui/dist /app/app/readmission-review-tracker/dist

EXPOSE 8080
CMD ["node", "src/index.js"]
