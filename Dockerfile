# Use an official Python runtime as a parent image
FROM python:3.9

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY ./app /app

# Install Python and system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python packages from requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Expose port 8060 to the outside world
EXPOSE 8060

# Define environment variable
ENV WORKERS=1
ENV MAX_REQUESTS=128
ENV MAX_REQUESTS_JITTER=16
ENV LIMIT_CONCURRENCY=5
ENV LIMIT_CONCURRENCY_JITTER=3

# Set the command to run your FastAPI application with Uvicorn and environment variables
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers $WORKERS --max-requests $MAX_REQUESTS --max-requests-jitter $MAX_REQUESTS_JITTER --limit-concurrency $LIMIT_CONCURRENCY --limit-concurrency-jitter $LIMIT_CONCURRENCY_JITTER"]
