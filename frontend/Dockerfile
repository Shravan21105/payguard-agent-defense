# ==============================================================================
# PAYGUARD Frontend — Production Multi-Stage Dockerfile
# ==============================================================================

# ------------------------------------------------------------------------------
# Stage 1: Build Static Assets
# ------------------------------------------------------------------------------
FROM node:20-alpine AS builder

WORKDIR /app

# Copy dependency specifications
COPY package.json package-lock.json* ./

# Install dependencies cleanly
RUN npm ci

# Copy configuration and source files
COPY tsconfig*.json vite.config.ts postcss.config.js tailwind.config.js ./
COPY index.html ./
COPY public/ ./public/
COPY src/ ./src/

# Support build-time public URL overrides
ARG VITE_API_URL="/api"
ARG VITE_WS_URL="/ws/events"
ENV VITE_API_URL=$VITE_API_URL
ENV VITE_WS_URL=$VITE_WS_URL

# Build production bundle (TypeScript verification + Vite minification)
RUN npm run build

# ------------------------------------------------------------------------------
# Stage 2: Serve with Production Nginx
# ------------------------------------------------------------------------------
FROM nginx:alpine AS runner

# Remove default nginx html
RUN rm -rf /usr/share/nginx/html/*

# Copy custom reverse proxy & SPA configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy compiled static assets from builder
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80

# Lightweight healthcheck using wget
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD wget -q --spider http://localhost:80/ || exit 1

CMD ["nginx", "-g", "daemon off;"]

