# syntax=docker/dockerfile:1.4

FROM python:3.10-slim as builder

WORKDIR /app

COPY requirements.txt .

ARG GITEA_REPOSITORY
ARG GITEA_REF_NAME

RUN python -m venv /app/venv && \
    . /app/venv/bin/activate && \
    --mount=type=cache,target=/opt/hostedtoolcache/pip \
    PIP_CACHE_DIR=/opt/hostedtoolcache/${GITEA_REPOSITORY}-${GITEA_REF_NAME}/pip \
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
