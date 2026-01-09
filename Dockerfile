# Use Node.js to build frontend, then Python to run backend
FROM node:20-slim AS frontend-builder

# Build frontend
WORKDIR /app
COPY package*.json ./
COPY vite.config.ts tsconfig*.json ./
COPY tailwind.config.ts postcss.config.js components.json ./
COPY index.html ./
COPY public/ ./public/
COPY src/ ./src/
# Set production environment variables for Vite build
ENV VITE_USE_MOCK_API=false
# Install dependencies (including devDependencies needed for build)
RUN npm ci --include=dev
# Set NODE_ENV for the build process
ENV NODE_ENV=production
RUN npm run build

# Use Python 3.11 for backend
FROM python:3.11-slim

# Set non-interactive frontend for apt-get to avoid debconf warnings
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies for pgvector
RUN apt-get update && apt-get install -y \
    postgresql-client \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copy backend code
COPY backend/ ./backend/

# Copy built frontend from builder stage
COPY --from=frontend-builder /app/dist ./dist
COPY --from=frontend-builder /app/public ./public

# Set working directory to backend for running the app
WORKDIR /app/backend

# Expose port (Railway will set PORT env var)
EXPOSE 8080

# Run the application
# Railway automatically sets PORT env var - use it
# Using exec form with shell to properly expand PORT variable
CMD ["sh", "-c", "exec python3 -m uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}"]

