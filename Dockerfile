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

# Environment variable for model caching
ENV TRANSFORMERS_CACHE=/app/models

# Assuming 'fastembed' is the correct library and 'FastEmbed' is the right class to use
# Adjust these commands according to the actual library and class names
RUN python -c "from fastembed import TextEmbedding; TextEmbedding('all-MiniLM-L6-v2')"

# Expose port 80 to the outside world
EXPOSE 80

# Command to run the app using Gunicorn with Uvicorn workers
CMD ["gunicorn", "main:app", "--worker-class", "uvicorn.workers.UvicornWorker", "--workers", "4", "--bind", "0.0.0.0:80"]
