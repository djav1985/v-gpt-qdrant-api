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
ENV WORKERS=2
ENV MAX_REQUESTS=128
ENV LIMIT_CONCURRENCY=32

# Set the command to run your FastAPI application with Uvicorn and environment variables
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port 8060 --workers $WORKERS --limit-max-requests $MAX_REQUESTS --limit-concurrency $LIMIT_CONCURRENCY"]
