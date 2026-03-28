FROM python:3.14.3-slim@sha256:fb83750094b46fd6b8adaa80f66e2302ecbe45d513f6cece637a841e1025b4ca AS base

FROM base AS builder
COPY requirements.txt .
RUN pip install --prefix="/install" -r requirements.txt

FROM base
WORKDIR /app
COPY --from=builder /install /usr/local
COPY . .

ENV PYTHONUNBUFFERED=0
ENV LOG_LEVEL=info
ENV PORT=8080

CMD gunicorn -b :$PORT --threads 4 --log-config logging.conf --log-level=$LOG_LEVEL "app:create_app()"
