# Dockerfile for Python Application
# Stage 1: Build environment
FROM python:3.11-alpine AS build
WORKDIR /app

# Install build dependencies and Python packages in a single RUN command
# Combining these commands reduces image layers and improves build performance
RUN apk add --no-cache --virtual .build-deps gcc musl-dev linux-headers \
    && pip install --no-cache-dir -r requirements.txt \
    && apk del .build-deps

# Copy application files into the WORKDIR
COPY . .

# Stage 2: Runtime environment
FROM python:3.11-alpine
WORKDIR /app

# Copy only necessary files from the build stage into the WORKDIR
COPY --from=build /app .

# Expose port 8000 for the application
EXPOSE 8000

# Command to run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
