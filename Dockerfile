# syntax=docker/dockerfile:1.4

FROM python:3.10-slim as builder

WORKDIR /app

COPY requirements.txt .

# Install dependencies into venv – build cache will reuse this layer
RUN python -m venv /app/venv && \
    . /app/venv/bin/activate && \
    pip install -r requirements.txt

FROM python:3.10-slim

WORKDIR /app

COPY --from=builder /app/venv /app/venv
COPY ./app /app

EXPOSE 8888

ENV WORKERS=2
ENV UVICORN_CONCURRENCY=32
ENV PATH="/app/venv/bin:$PATH"

CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port 8888 --workers $WORKERS --limit-concurrency $UVICORN_CONCURRENCY"]
