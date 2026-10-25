
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY bajalo/requirements.txt ./requirements.txt

RUN pip install --no-cache-dir -r requirements.txt

COPY bajalo/ ./

EXPOSE 10000

CMD ["sh", "-c", "waitress-serve --listen=0.0.0.0:${PORT:-10000} app:app"]
