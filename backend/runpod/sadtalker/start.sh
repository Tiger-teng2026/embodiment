#!/bin/bash
# 先用持久卷里的权重。卷上没有时，从镜像内置副本复制；副本也没有才下载一次。
set -euo pipefail

VOLUME="${SADTALKER_MODEL_DIR:-/workspace/sadtalker}"
BUNDLED="${SADTALKER_BUNDLED_DIR:-/opt/sadtalker-weights}"
MARKER="${VOLUME}/checkpoints/SadTalker_V0.0.2_256.safetensors"
PORT="${PORT:-8000}"

mkdir -p "${VOLUME}/checkpoints" "${VOLUME}/gfpgan/weights" "${SADTALKER_OUTPUT_DIR:-/workspace/outputs}"

if [ ! -s "${MARKER}" ]; then
  if [ -s "${BUNDLED}/checkpoints/SadTalker_V0.0.2_256.safetensors" ]; then
    echo "从镜像复制权重到持久卷"
    cp -a "${BUNDLED}/checkpoints/." "${VOLUME}/checkpoints/"
    cp -a "${BUNDLED}/gfpgan/weights/." "${VOLUME}/gfpgan/weights/"
  else
    echo "持久卷和镜像都没有权重，开始下载"
    bash /opt/sadtalker/download_weights.sh "${VOLUME}"
  fi
fi

if [ ! -s "${MARKER}" ]; then
  echo "权重仍不可用" >&2
  exit 1
fi

if [ -d /opt/sadtalker/checkpoints ] && [ ! -L /opt/sadtalker/checkpoints ]; then
  rm -rf /opt/sadtalker/checkpoints
fi
if [ -d /opt/sadtalker/gfpgan ] && [ ! -L /opt/sadtalker/gfpgan ]; then
  rm -rf /opt/sadtalker/gfpgan
fi
ln -sfn "${VOLUME}/checkpoints" /opt/sadtalker/checkpoints
ln -sfn "${VOLUME}/gfpgan" /opt/sadtalker/gfpgan

export SADTALKER_CHECKPOINT_DIR="${VOLUME}/checkpoints"
export SADTALKER_HOME=/opt/sadtalker
cd /opt/infer
exec python3 -m uvicorn app:app --host 0.0.0.0 --port "${PORT}" --proxy-headers --forwarded-allow-ips="*"
