"""启动推理前确认画面里有一张可用的正脸。"""

from __future__ import annotations

from pathlib import Path


class FaceMissing(Exception):
    pass


def assert_one_face(image_path: Path) -> None:
    import cv2

    image = cv2.imread(str(image_path))
    if image is None:
        raise FaceMissing()
    height, width = image.shape[:2]
    long_side = max(height, width)
    if long_side > 960:
        scale = 960 / long_side
        image = cv2.resize(image, (max(1, int(width * scale)), max(1, int(height * scale))))
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    boxes = cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(48, 48))
    if len(boxes) != 1:
        raise FaceMissing()
    _x, _y, _w, face_h = boxes[0]
    if face_h < image.shape[0] * 0.08:
        raise FaceMissing()
