# utils.py
import numpy as np
from PIL import Image


def get_webcam_frame() -> np.ndarray:
    import xospy
    cam_w, _ = xospy.video.webcam.get_resolution()
    cam_bytes = xospy.video.webcam.get_frame()
    bytes_per_pixel = 3
    total_pixels = len(cam_bytes) // bytes_per_pixel
    cam_h = total_pixels // cam_w

    if cam_w * cam_h * bytes_per_pixel != len(cam_bytes):
        raise Exception("Webcam resolution doesn't match buffer size. Skipping.")

    cam_array = np.frombuffer(cam_bytes, dtype=np.uint8).reshape((cam_h, cam_w, 3))

    scale = cam_h / 256
    new_w = int(cam_w / scale)
    new_h = 256
    cam_array = np.array(Image.fromarray(cam_array).resize((new_w, new_h), Image.LANCZOS))

    cam_array = cam_array[:, ::-1]  # horizontal flip
    cam_array = np.mean(cam_array, axis=2).astype(np.uint8)
    cam_array = np.expand_dims(cam_array, axis=2)

    return cam_array


def draw_cross(frame: np.ndarray, x: float, y: float, size: int = 10, color=(255, 0, 0, 255)):
    height, width, _ = frame.shape
    x, y = int(x), int(y)

    for dx in range(-size, size + 1):
        xi = x + dx
        if 0 <= xi < width and 0 <= y < height:
            frame[y, xi] = color

    for dy in range(-size, size + 1):
        yi = y + dy
        if 0 <= x < width and 0 <= yi < height:
            frame[yi, x] = color
