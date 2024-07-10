<<<<<<< HEAD
# Use a slimmer Python image as base
FROM python:3.9-slim as base
=======
# Build stage
FROM python:3.10-slim as builder
>>>>>>> main

# Set the working directory
WORKDIR /app

<<<<<<< HEAD
# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libffi-dev \
    libssl-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy only the requirements file
COPY ./requirements.txt /app/

# Install Python dependencies
RUN --mount=type=cache,target=/root/.cache/pip pip install --no-cache-dir -r requirements.txt
=======
# Copy the requirements file and cache
COPY /cache /app/cache
COPY requirements.txt /app

# Install Python dependencies in a virtual environment
RUN python -m venv /app/venv && \
    . /app/venv/bin/activate && \
    pip install --no-index --find-links /app/cache -r requirements.txt

# Final stage
FROM python:3.10-slim

# Set the working directory
WORKDIR /app

# Copy the virtual environment from the builder stage
COPY --from=builder /app/venv /app/venv
>>>>>>> main

# Copy the rest of the application
COPY ./app /app

<<<<<<< HEAD
# Expose port 8060 to the outside world
EXPOSE 8060
=======
# Expose port 8040 to the outside world
EXPOSE 8888
>>>>>>> main

# Define environment variables
ENV WORKERS=2
ENV UVICORN_CONCURRENCY=32
<<<<<<< HEAD

# Set the command to run your FastAPI application with Uvicorn and environment variables
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port 8060 --workers $WORKERS --limit-concurrency $UVICORN_CONCURRENCY --timeout-keep-alive 32"]
=======
ENV PATH="/app/venv/bin:$PATH"

# Set the command to run your FastAPI application with Uvicorn
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port 8888 --workers $WORKERS --limit-concurrency $UVICORN_CONCURRENCY"]
>>>>>>> main
