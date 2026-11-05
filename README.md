# 化身 Embodiment

原声数字人口播。上传人像和你自己的 mp3，只驱动画面，音频原样混流。当前是自用版本：简易登录，没有公开注册。界面中英双语，默认中文。

单段最长 30 秒。可以微调口型时间偏移。成片烧录水印「化身 Embodiment AI合成内容」，并在元数据里标记为 AI 深度合成。

GPU 推理跑在 Runpod 的 RTX 4090 Pod 里。步骤和要填的环境变量在 `backend/RUNPOD.md`。LivePortrait 只驱动口部，用户的 mp3 由 ffmpeg 原样混流。

## 环境

需要 Python 3.11 或更新、Node.js 20 或更新、Docker、以及能执行 `ffmpeg -version` 的 ffmpeg。Windows 自带的 `WindowsApps\python.exe` 只是商店占位，不能建虚拟环境。装好后新开一个终端，确认 `python --version` 是 3.11 以上。

```powershell
winget install -e --id Python.Python.3.12
winget install -e --id Gyan.FFmpeg
winget install -e --id Docker.DockerDesktop
```

Docker Desktop 装完后先打开一次，等引擎起来再执行 `docker compose`。

## 目录

```
frontend/     Vite + React + Tailwind + react-i18next
backend/      FastAPI + Celery + Redis + MinIO + LivePortrait
backend/inference/   LivePortrait、rembg、ffmpeg 混流
docker-compose.yml   本地 Redis 与 MinIO
```

默认账号在 `backend/.env`：`admin` / `embodiment`。给别人用之前先改掉 `ADMIN_PASSWORD` 和 `SECRET_KEY`。

## 初始化

在项目根目录 `D:\AI\embodiment` 执行。已改过 `.env` 时，不要再次覆盖。

```powershell
cd D:\AI\embodiment
Copy-Item backend\.env.example backend\.env
Copy-Item frontend\.env.example frontend\.env
docker compose up -d
python -m venv backend\.venv
backend\.venv\Scripts\python -m pip install -r backend\requirements.txt
cd frontend
npm install
cd ..
```

启动命令直接调用 `backend\.venv\Scripts\` 下的程序，不需要 Activate。

## 启动

开三个终端。没有 NVIDIA GPU 时，worker 会在推理阶段失败。LivePortrait 的正式运行环境是 Runpod 容器，见 `backend/RUNPOD.md`。

终端 1，API：

```powershell
cd D:\AI\embodiment\backend
.\.venv\Scripts\uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

终端 2，队列。Windows 必须加 `--pool=solo`。

```powershell
cd D:\AI\embodiment\backend
.\.venv\Scripts\celery -A app.celery_app worker --loglevel=info --pool=solo
```

终端 3，页面：

```powershell
cd D:\AI\embodiment\frontend
npm run dev
```

- 页面：http://localhost:5173
- 接口文档：http://127.0.0.1:8000/docs
- MinIO 控制台：http://localhost:9001 （minioadmin / minioadmin）

手机和电脑同一 Wi-Fi 时，用电脑的局域网地址打开 `http://<电脑IP>:5173`。下载链接默认指向本机 MinIO。手机要能下载时，把 `MINIO_PUBLIC_ENDPOINT` 设成 `<电脑IP>:9000`，并放行防火墙的 5173 和 9000 端口。

## 页面

- `/login` 登录
- `/` 创建任务
- `/history` 任务历史
- `/agreement` 使用说明与合成内容声明

右上角切换中文 / English。文案在 `frontend/src/locales/zh.json` 和 `en.json`。

## 生成规则

两种模式：

- `original_bg`：沿用自拍原图背景
- `preset_scene`：预设场景。可选 `studio_soft`、`office_day`、`city_night`、`home_warm`

上传 JPG / PNG / WEBP，以及 MP3。超过 30 秒时页面直接拦住，后端会再查一次。口型偏移范围是 -1000 到 1000 毫秒。正值延迟音频，负值延迟画面。音频使用 ffmpeg `-c:a copy`，不重新编码。

## 接口

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/api/health` | 服务、Redis、MinIO |
| GET | `/api/meta` | 时长、大小、偏移、水印 |
| POST | `/api/auth/login` | 登录，返回 token |
| GET | `/api/auth/me` | 当前用户 |
| GET | `/api/tasks/templates` | 场景模板 |
| POST | `/api/create-task` | 创建任务，multipart。`POST /api/tasks` 是同一接口 |
| GET | `/api/tasks/list` | 最近任务。`GET /api/tasks` 是同一接口 |
| GET | `/api/task/{id}` | 单条任务，成功时带 `video_url`。`GET /api/tasks/{id}` 是同一接口 |
| GET | `/api/tasks/{id}/download` | 预签名下载地址 |

错误体是 `{"detail": {"code": "AUDIO_TOO_LONG"}}`。页面按 code 显示中英文文案。

## 部署预留

前端可以放到 Vercel。`frontend/vercel.json` 已做单页回退。本地默认 `VITE_BACKEND_API_URL=mock`，只模拟界面。对接后端时把它设成 Pod 的 HTTP 地址，末尾不要斜杠。API 的 `CORS_ORIGINS` 要带上这个页面来源。

GPU 部署见 `backend/RUNPOD.md`。MinIO 预签名地址必须能从浏览器和 Runpod 访问，本机 `localhost` 不行。
