# RTX 4090 pod. Torch comes from the base image; do not pip-install a CPU torch over it.
FROM pytorch/pytorch:2.4.1-cuda12.4-cudnn9-runtime

ARG HF_ENDPOINT=https://huggingface.co
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    LIVEPORTRAIT_HOME=/opt/LivePortrait \
    HF_ENDPOINT=${HF_ENDPOINT} \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ffmpeg \
        git \
        redis-server \
        fonts-noto-cjk \
        libgl1 \
        libglib2.0-0 \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

RUN git clone --depth 1 https://github.com/KlingAIResearch/LivePortrait.git /opt/LivePortrait \
    && pip install --no-cache-dir -r /opt/LivePortrait/requirements_base.txt -i https://pypi.tuna.tsinghua.edu.cn/simple \
    && huggingface-cli download KlingTeam/LivePortrait \
        --local-dir /opt/LivePortrait/pretrained_weights \
        --exclude "*.git*" "README.md" "docs" \
    && python -c "from rembg import new_session; new_session('u2net', providers=['CPUExecutionProvider'])"

COPY . .
RUN chmod +x /app/start.sh \
    && mkdir -p /data/work

EXPOSE 8000
CMD ["/app/start.sh"]
