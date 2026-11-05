# Runpod RTX 4090 部署

这是一个 GPU Pod，不是 Serverless。容器里按顺序启动 Redis、Celery Worker、FastAPI。MinIO 不在容器里，要事先准备好，并让 Pod 能访问。

LivePortrait 用一段人脸视频驱动口部，再把用户自己的 mp3 原样混进成片。音频不会送去做语音合成或音色克隆。口型跟随驱动视频，不是按音素对齐。默认驱动视频是 LivePortrait 自带的 `d0.mp4`。如果要更像说话，把一段正脸、开头中性表情的 mp4 放进容器，设置 `LIVEPORTRAIT_DRIVING` 为它的路径。

## 镜像

在能访问 GitHub 和 Hugging Face 的机器上构建。国内网络可以加镜像参数：

```bash
docker build -f backend/Dockerfile \
  --build-arg HF_ENDPOINT=https://hf-mirror.com \
  -t embodiment-backend:4090 backend
```

构建会下载 PyTorch CUDA 基础镜像、LivePortrait 源码和 `KlingTeam/LivePortrait` 权重，以及 rembg 的 u2net。镜像体积大，第一次构建需要一段时间。本仓库这台 Windows 机器没有 Docker，这里没有实际构建过。

把镜像推到 Runpod 能拉取的仓库，然后新建 Pod：

- GPU：RTX 4090
- 镜像：`embodiment-backend:4090`
- 容器磁盘：建议 80 GB 以上
- 暴露 HTTP 端口：`8000`
- 启动命令留空，使用镜像里的 `/app/start.sh`
- 可选卷：挂到 `/data`，用来保留 SQLite 和 Redis

`start.sh` 的顺序是：启动本机 Redis 并等待 `PONG`，后台启动 `celery --pool=solo --concurrency=1`，前台启动 uvicorn。`--pool=solo` 避免 CUDA 在 fork 之后出错。Redis 锁 `embodiment:gpu` 再保证同一时刻只有一个推理。

## 面板环境变量

必填：

| 变量 | 填什么 |
| --- | --- |
| `ADMIN_USERNAME` | 自用登录名 |
| `ADMIN_PASSWORD` | 自用密码。示例里的 `embodiment` 只适合本机，对外前要改掉 |
| `SECRET_KEY` | 一长串随机字符串，用来签登录 token |
| `REDIS_URL` | `redis://127.0.0.1:6379/0`。这是容器内 Redis。不要填 `localhost` 以外的地址，除非你不用容器里的 Redis |
| `GPU_DEVICE_ID` | `0`。Pod 只有一张 4090 时就是 0 |
| `MINIO_ENDPOINT` | MinIO 的 `主机:端口`，不要带 `http://`。Pod 必须能连上，不能填你电脑上的 `localhost` |
| `MINIO_ACCESS_KEY` | MinIO Access Key |
| `MINIO_SECRET_KEY` | MinIO Secret Key |
| `MINIO_BUCKET_NAME` | 桶名，例如 `embodiment`。不存在时服务会创建 |

按需填写：

| 变量 | 填什么 |
| --- | --- |
| `MINIO_SECURE` | 走 HTTPS 时填 `true`，否则 `false` |
| `MINIO_PUBLIC_ENDPOINT` | 浏览器下载用的 `主机:端口`。和 `MINIO_ENDPOINT` 相同时留空 |
| `CORS_ORIGINS` | 前端页面来源。本地 Vite 是 `http://localhost:5173,http://127.0.0.1:5173`。多个用逗号隔开。填 `*` 表示不限制 |
| `LIVEPORTRAIT_HOME` | 默认 `/opt/LivePortrait`，一般不用改 |
| `LIVEPORTRAIT_DRIVING` | 可选。替换默认口型驱动视频的绝对路径 |
| `FONT_PATH` | 可选。水印字体。镜像里会找 Noto CJK |
| `DATABASE_URL` | 默认 `sqlite:////data/embodiment.db` |

密钥只从环境变量读取，镜像和代码里不写默认密码。

## 接口

登录后，除登录外的请求都带 `Authorization: Bearer <token>`。

现有前端还在用原来的路径，这些路径仍然可用。下面每组是同一个处理函数：

- `POST /api/auth/login`
- `POST /api/create-task`，同时保留 `POST /api/tasks`
- `GET /api/task/{taskId}`，同时保留 `GET /api/tasks/{taskId}`。成功时 `video_url` 是预签名地址
- `GET /api/tasks/list`，同时保留 `GET /api/tasks`
- 另外还有 `GET /api/health`、`GET /api/meta`、`GET /api/auth/me`、`GET /api/tasks/templates`、`GET /api/tasks/{taskId}/download`

创建任务是 multipart：`portrait`、`audio`、`mode`（`original_bg` 或 `preset_scene`）、`offset_ms`（-1000 到 1000）、`template_id`（预设场景时必填：`studio_soft`、`office_day`、`city_night`、`home_warm`）。mp3 超过 30 秒会拒绝。

前端对接时把 `VITE_BACKEND_API_URL` 设成 Pod 的 HTTP 地址，末尾不要斜杠，然后重启前端。

```bash
curl -s -X POST "$API/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"你的密码"}'

curl -s -X POST "$API/api/create-task" \
  -H "Authorization: Bearer $TOKEN" \
  -F "mode=original_bg" \
  -F "offset_ms=0" \
  -F "portrait=@portrait.jpg" \
  -F "audio=@voice.mp3"
```

## 用量和订阅

`backend/app/billing.py` 的 `UsageLedger.authorize` 在创建任务时调用，现在直接放行。`record` 在任务成功或失败时写一条日志，参数是用户、任务号、音频秒数和状态。以后做额度时只改这个文件：超额就在 `authorize` 里拒绝，`record` 里落账。任务上已经有 `owner` 字段。
