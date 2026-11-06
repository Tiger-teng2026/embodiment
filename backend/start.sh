#!/bin/bash
set -euo pipefail

# ========= 新增：启动的时候再安装gcc/g++编译套件 =========
apt-get update
apt-get install -y --no-install-recommends build-essential

# 安装 onnxruntime-gpu，3次重试
ort_installed=0
for attempt in 1 2 3; do
  if pip install --no-cache-dir onnxruntime-gpu==1.19.2 -i https://pypi.tuna.tsinghua.edu.cn/simple; then
    ort_installed=1
    break
  fi
  if [ "$attempt" -lt 3 ]; then
    echo "onnxruntime-gpu install failed, retry ${attempt}/2" >&2
    sleep 2
  fi
done
if [ "$ort_installed" -ne 1 ]; then
  echo "onnxruntime-gpu install failed after 2 retries" >&2
  exit 1
fi

# ========= 新增：启动阶段安装 insightface，在这里编译，不在镜像构建阶段编译 =========
ins_installed=0
for attempt in 1 2 3; do
  if pip install --no-cache-dir insightface==0.7.3 -i https://pypi.tuna.tsinghua.edu.cn/simple; then
    ins_installed=1
    break
  fi
  if [ "$attempt" -lt 3 ]; then
    echo "insightface install failed, retry ${attempt}/2" >&2
    sleep 3
  fi
done
if [ "$ins_installed" -ne 1 ]; then
  echo "insightface install failed after 2 retries" >&2
  exit 1
fi

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
