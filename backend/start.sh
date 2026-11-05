#!/bin/bash
set -euo pipefail

mkdir -p /data/work /data
export CUDA_VISIBLE_DEVICES="${GPU_DEVICE_ID:-0}"
export PYTHONPATH="/app${PYTHONPATH:+:$PYTHONPATH}"

if [ -z "${REDIS_URL:-}" ]; then
  export REDIS_URL="redis://127.0.0.1:6379/0"
fi

redis-server \
  --daemonize yes \
  --bind 127.0.0.1 \
  --port 6379 \
  --protected-mode yes \
  --dir /data \
  --dbfilename redis.rdb \
  --save 60 1

ready=0
for _ in $(seq 1 50); do
  if redis-cli ping 2>/dev/null | grep -q PONG; then
    ready=1
    break
  fi
  sleep 0.2
done
if [ "$ready" -ne 1 ]; then
  echo "redis did not start" >&2
  exit 1
fi

cd /app
celery -A app.celery_app:app worker \
  --loglevel=INFO \
  --pool=solo \
  --concurrency=1 \
  --hostname=embodiment@%h &

exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
