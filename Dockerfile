# Stage 1: Build environment
FROM python:3.11-alpine AS build
WORKDIR /app
# Copy the current directory contents into the container at /app
COPY ./app /app

# Install build dependencies and Python packages in a single RUN command
RUN apk update && \
    apk add --no-cache --virtual .build-deps gcc musl-dev linux-headers \
    && pip install --no-cache-dir -r /app/requirements.txt \
    && apk del .build-deps

# Stage 2: Runtime environment
FROM python:3.11-alpine
WORKDIR /app
# Copy only the necessary files from the build stage
COPY --from=build /app .

# Expose the port Uvicorn will run on
EXPOSE 80

# Command to run the application using Uvicorn directly
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]