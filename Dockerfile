# Use an official Python runtime as a parent image
FROM python:3.9

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY ./app /app

# Install system dependencies required for Python packages
RUN apt-get update && apt-get install -y \
    gcc \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python packages from requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Set an environment variable for the cache directory
ENV TRANSFORMERS_CACHE=/app/models

# Pre-download the model
RUN python -c "from fastembed import FastEmbed; FastEmbed(model_name='all-MiniLM-L6-v2')"

# Expose port 80 to the outside world
EXPOSE 80

# Run the application with Gunicorn using Uvicorn workers
CMD ["gunicorn", "main:app", "--worker-class", "uvicorn.workers.UvicornWorker", "--workers", "4", "--bind", "0.0.0.0:80"]
