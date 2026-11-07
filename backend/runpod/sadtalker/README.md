# Embodiment SadTalker

单张人像加一段音频，生成无声对口型画面。音频混流、变调和水印都在 embodiment 主后端完成，这个服务不处理 TTS，也不做音色克隆。

## 接口

`GET /health` 给 Runpod 探活。权重就绪时返回 `{"ok": true}`。

`POST /infer`

```json
{
  "source_image_url": "https://example.com/portrait.jpg",
  "audio_file_url": "https://example.com/voice.mp3",
  "audio_offset": -180,
  "max_duration": 30
}
```

成功时返回：

```json
{"video_url": "https://<pod>-8000.proxy.runpod.net/outputs/<id>.mp4"}
```

`audio_offset` 单位是毫秒，范围 -1000 到 1000。正值让口型延后，负值让口型提前，只移动画面。`max_duration` 最大 30，更长的驱动音频会被截断。无人脸返回 HTTP 422，正文码是 `FACE_NOT_DETECTED`。推理超过 `INFER_TIMEOUT_SECONDS`（默认 180 秒）返回 HTTP 504，正文码是 `GPU_TIMEOUT`。GPU 正在忙时返回 HTTP 429。

主后端拿到这个无声 MP4 后，把用户原来的 MP3 以流复制方式混进去，不再做第二次时间偏移。本地没有配置 Runpod 时，主后端仍用模拟画面，并在混流时应用同一条偏移。

设置了 `INFERENCE_API_KEY` 之后，`/infer` 和 `/outputs` 都要带 `Authorization: Bearer <同一把密钥>`。`/health` 不校验密钥。

## 构建镜像

在本目录执行：

```bash
docker build -t your-registry/embodiment-sadtalker:latest .
docker push your-registry/embodiment-sadtalker:latest
```

基础镜像是 `nvidia/cuda:12.1.1-cudnn8-runtime-ubuntu22.04`，里面有 Python、ffmpeg 和 CUDA 版 PyTorch。构建时会把 SadTalker 官方权重复制进镜像。容器启动时优先使用挂在 `/workspace` 的持久卷；卷上没有权重时，从镜像复制一次，不再每次启动重新下载。

## 在 Runpod 创建 Pod

1. 打开 [Runpod 控制台](https://www.runpod.io/console/pods)，选择 Deploy，镜像填刚推送的地址。
2. GPU 选 **NVIDIA A10G**。容器盘 50 GB。Network Volume 至少 **40 GB**，挂载路径 `/workspace`。`runpod.json` 里是同一组参数。
3. 暴露 HTTP 端口 **8000**。
4. 环境变量：
   - `SADTALKER_MODEL_DIR=/workspace/sadtalker`
   - `SADTALKER_OUTPUT_DIR=/workspace/outputs`
   - `PORT=8000`
   - `INFER_TIMEOUT_SECONDS=180`
   - `INFERENCE_API_KEY` 设成一串随机密钥
   - `PUBLIC_BASE_URL` 先留空，Pod 起来后再填代理地址
5. 启动命令保持 `/opt/infer/start.sh`。
6. Pod 运行后，在 Connect 里复制 HTTP 代理地址，形如 `https://<podid>-8000.proxy.runpod.net`。把这个地址写回 Pod 的 `PUBLIC_BASE_URL`，然后重启一次 Pod，这样返回的 `video_url` 才能被主后端下载。
7. 浏览器或 curl 访问 `https://<podid>-8000.proxy.runpod.net/health`，看到 `{"ok": true}` 即探活通过。

## 拿到 API Key 并写进主后端

1. 打开 Runpod 右上角 Settings → API Keys，Create API Key。这把钥匙用于 Runpod 自己的账号接口。
2. 推理服务使用的是 Pod 环境变量 `INFERENCE_API_KEY`。主后端要带同一把钥匙访问 `/infer`。
3. 在 `backend/.env` 填写后重启 FastAPI 和 Celery：

```env
RUNPOD_SADTALKER_ENDPOINT=https://<podid>-8000.proxy.runpod.net
RUNPOD_API_KEY=<与 INFERENCE_API_KEY 相同的密钥>
```

`RUNPOD_SADTALKER_ENDPOINT` 填服务根地址，不要加 `/infer`。主后端会请求 `POST /infer`，并传入对象存储里的图片和 MP3 预签名地址。生产环境必须使用 S3 兼容存储（例如 Cloudflare R2），Runpod 才能下载素材。开发环境这两项留空时，主后端继续用本地模拟视频，不访问 Runpod。
