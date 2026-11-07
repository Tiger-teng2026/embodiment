FROM nvidia/cuda:12.1.1-cudnn8-runtime-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    SADTALKER_MODEL_DIR=/workspace/sadtalker \
    SADTALKER_BUNDLED_DIR=/opt/sadtalker-weights \
    SADTALKER_OUTPUT_DIR=/workspace/outputs \
    SADTALKER_CHECKPOINT_DIR=/workspace/sadtalker/checkpoints \
    PORT=8000 \
    MAX_DURATION_SECONDS=30 \
    INFER_TIMEOUT_SECONDS=180

RUN apt-get update && apt-get install -y --no-install-recommends \
        python3 \
        python3-pip \
        python3-venv \
        ffmpeg \
        git \
        wget \
        unzip \
        ca-certificates \
        libgl1 \
        libglib2.0-0 \
        libsndfile1 \
    && ln -sf /usr/bin/python3 /usr/bin/python \
    && rm -rf /var/lib/apt/lists/*

RUN python3 -m pip install --upgrade pip \
    && python3 -m pip install --no-cache-dir \
        torch==2.1.2 torchvision==0.16.2 torchaudio==2.1.2 \
        --index-url https://download.pytorch.org/whl/cu121

WORKDIR /opt/sadtalker
RUN git clone --depth 1 https://github.com/OpenTalker/SadTalker.git /opt/sadtalker \
    && python3 -m pip install --no-cache-dir -r /opt/sadtalker/requirements.txt \
    && python3 -m pip install --no-cache-dir \
        torch==2.1.2 torchvision==0.16.2 torchaudio==2.1.2 \
        --index-url https://download.pytorch.org/whl/cu121 \
    && python3 -m pip install --no-cache-dir fastapi==0.115.6 uvicorn==0.32.1 opencv-python-headless==4.10.0.84

COPY download_weights.sh /opt/sadtalker/download_weights.sh
RUN chmod +x /opt/sadtalker/download_weights.sh \
    && bash /opt/sadtalker/download_weights.sh /opt/sadtalker-weights

COPY infer/ /opt/infer/
COPY start.sh /opt/infer/start.sh
RUN chmod +x /opt/infer/start.sh /opt/sadtalker/download_weights.sh

EXPOSE 8000
CMD ["/opt/infer/start.sh"]
