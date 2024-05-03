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
ENV MAX_CONNECTIONS=16
ENV MAX_REQUESTS=32
ENV MAX_REQUESTS_JITTER=8

CMD ["sh", "-c", "gunicorn main:app --worker-class uvicorn.workers.UvicornWorker --workers ${WORKERS} --worker-connections ${MAX_CONNECTIONS} --max-requests $MAX_REQUESTS --max-requests-jitter $MAX_REQUESTS_JITTER --bind 0.0.0.0:8060 --preload"]