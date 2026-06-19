# Stage 1: Build the React Dashboard
FROM node:20-alpine AS frontend-builder
WORKDIR /app/dashboard
COPY dashboard/package.json dashboard/package-lock.json* ./
RUN npm install
COPY dashboard/ ./
RUN npm run build

# Stage 2: Setup Python API and serve
FROM python:3.10-slim
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn

# Copy Python API code
COPY api/ ./api/
# Create necessary output directories
RUN mkdir -p /app/api/smc_output

# Copy the built React app from the first stage into a static folder
COPY --from=frontend-builder /app/dashboard/dist /app/api/static

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PORT=5000

# Expose the port
EXPOSE 5000

# Run gunicorn serving the Flask app
# The app is located in api/api.py, the module is 'api.api', and the app instance is 'app'
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "--timeout", "120", "api.api:app"]
