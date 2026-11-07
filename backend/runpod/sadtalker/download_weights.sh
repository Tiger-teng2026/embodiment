#!/bin/bash
# SadTalker 官方权重。已存在的文件不重复下载。
set -euo pipefail

ROOT="${1:-/opt/sadtalker-weights}"
CKPT="${ROOT}/checkpoints"
GFP="${ROOT}/gfpgan/weights"
mkdir -p "${CKPT}" "${GFP}"

fetch() {
  local url="$1"
  local dest="$2"
  if [ -s "${dest}" ]; then
    echo "已存在 $(basename "${dest}")"
    return 0
  fi
  echo "下载 $(basename "${dest}")"
  wget -q --show-progress -O "${dest}.partial" "${url}"
  mv "${dest}.partial" "${dest}"
}

fetch "https://github.com/OpenTalker/SadTalker/releases/download/v0.0.2-rc/mapping_00109-model.pth.tar" "${CKPT}/mapping_00109-model.pth.tar"
fetch "https://github.com/OpenTalker/SadTalker/releases/download/v0.0.2-rc/mapping_00229-model.pth.tar" "${CKPT}/mapping_00229-model.pth.tar"
fetch "https://github.com/OpenTalker/SadTalker/releases/download/v0.0.2-rc/SadTalker_V0.0.2_256.safetensors" "${CKPT}/SadTalker_V0.0.2_256.safetensors"
fetch "https://github.com/OpenTalker/SadTalker/releases/download/v0.0.2-rc/SadTalker_V0.0.2_512.safetensors" "${CKPT}/SadTalker_V0.0.2_512.safetensors"

fetch "https://github.com/xinntao/facexlib/releases/download/v0.1.0/alignment_WFLW_4HG.pth" "${GFP}/alignment_WFLW_4HG.pth"
fetch "https://github.com/xinntao/facexlib/releases/download/v0.1.0/detection_Resnet50_Final.pth" "${GFP}/detection_Resnet50_Final.pth"
fetch "https://github.com/xinntao/facexlib/releases/download/v0.2.2/parsing_parsenet.pth" "${GFP}/parsing_parsenet.pth"
fetch "https://github.com/TencentARC/GFPGAN/releases/download/v1.3.0/GFPGANv1.4.pth" "${GFP}/GFPGANv1.4.pth"

test -s "${CKPT}/SadTalker_V0.0.2_256.safetensors"
echo "权重就绪 ${ROOT}"
