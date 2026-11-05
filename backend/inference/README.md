# 推理

`run_inference` 按这个顺序执行：

1. `original_bg` 保留照片。`preset_scene` 用 rembg 抠人像，贴到 1280×720 的场景上。场景图放在 `assets/scenes/{template_id}.png`，没有图时用模板色。
2. LivePortrait 只驱动口部。驱动源是一段人脸视频，默认用仓库里的 `assets/examples/driving/d0.mp4`，按音频时长循环后截断。模型不接收 mp3，口型不是按音素对齐。
3. ffmpeg 丢掉驱动视频自带的声音，把用户原始 mp3 以 `acodec=copy` 混进去。正偏移延迟音频，负偏移延迟画面。画面烧录「化身 Embodiment AI合成内容」，并写入 AI 深度合成元数据。

GPU 任务由 Celery solo worker 串行执行，同时只有一个推理。部署步骤见 `backend/RUNPOD.md`。
