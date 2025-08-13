import os
import re
import json
import base64
from datetime import datetime


def slugify(text: str) -> str:
    if not text:
        return "topic"
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = re.sub(r"-+", "-", text).strip("-")
    return text or "topic"


def get_timestamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def get_output_root() -> str:
    return os.getenv("OUTPUT_ROOT", "outputs")


def create_output_dir(topic: str, base_output_root: str | None = None) -> str:
    root = base_output_root or get_output_root()
    os.makedirs(root, exist_ok=True)
    folder = f"{get_timestamp()}_{slugify(topic)}"
    path = os.path.join(root, folder)
    os.makedirs(path, exist_ok=True)
    return path


def save_json(path: str, obj: dict) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


def save_text(path: str, text: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def save_base64_image(path: str, b64_string: str) -> None:
    data = base64.b64decode(b64_string)
    with open(path, "wb") as f:
        f.write(data)


