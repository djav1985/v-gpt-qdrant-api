# Use an official Python runtime based on Alpine as a parent image
FROM python:3.10-alpine

# Set the working directory in the container
WORKDIR /app

# Install system dependencies
RUN apk add --no-cache gcc musl-dev python3-dev libffi-dev openssl-dev

# Copy the requirements file and install Python dependencies
COPY ./app/requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Remove build dependencies to reduce image size
RUN apk del gcc musl-dev python3-dev libffi-dev openssl-dev

# Copy the current directory contents into the container at /app
COPY ./app /app

# Expose port 80 to the outside world
EXPOSE 80

# Run the application with Gunicorn using Uvicorn workers
CMD ["gunicorn", "main:app", "--worker-class", "uvicorn.workers.UvicornWorker", "--workers", "4", "--bind", "0.0.0.0:80"]
