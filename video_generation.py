"""Optional cloud text/image-to-video generation through Replicate's LTX 2.3 Fast.

The engine remains local for story direction, timeline, audio and editing. This
adapter uses a remote GPU only when --generate-video is explicitly requested.
"""
from __future__ import annotations

import base64
import io
import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

API = "https://api.replicate.com/v1/models/lightricks/ltx-2.3-fast/predictions"

def camera_motion(direction: str) -> str:
    mapping = {
        "slow_push_in": "dolly_in",
        "subtle_push_in": "dolly_in",
        "slow_pull_back": "dolly_out",
        "slow_track": "dolly_right",
        "slow_pan": "dolly_left",
        "slow_rack_focus": "focus_shift",
    }
    return mapping.get(str(direction or ""), "none")

def image_data_uri(image: Any, max_bytes: int = 245_000) -> str:
    """Compress a PIL image into Replicate's documented small-file data-URL form."""
    from PIL import Image
    im = image.convert("RGB")
    for size in ((768, 432), (640, 360), (512, 288)):
        candidate = im.copy()
        candidate.thumbnail(size, Image.Resampling.LANCZOS)
        for quality in (78, 65, 52, 40):
            buf = io.BytesIO()
            candidate.save(buf, format="JPEG", quality=quality, optimize=True)
            raw = buf.getvalue()
            if len(raw) <= max_bytes:
                return "data:image/jpeg;base64," + base64.b64encode(raw).decode("ascii")
    raise ValueError("Could not compress scene reference image below Replicate's 256 KB data-URL limit.")

def _request(url: str, token: str, method: str = "GET", payload: dict | None = None,
             prefer_wait: bool = False) -> dict:
    headers = {"Authorization": "Bearer " + token, "Content-Type": "application/json"}
    if prefer_wait:
        headers["Prefer"] = "wait=60"
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=180) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")[:1500]
        raise RuntimeError(f"Replicate API returned HTTP {exc.code}: {detail}") from exc

def generate_video(prompt: str, reference_image: Any, output_path: str | Path,
                   duration: int = 6, camera: str = "none", poll_seconds: int = 5,
                   timeout_seconds: int = 1200) -> Path:
    """Generate one MP4 scene, reusing a still as the first frame for visual continuity."""
    token = os.environ.get("REPLICATE_API_TOKEN")
    if not token:
        raise RuntimeError(
            "REPLICATE_API_TOKEN is missing. Set it in PowerShell before using --generate-video."
        )
    if duration not in {6, 8, 10, 12, 14, 16, 18, 20}:
        raise ValueError("LTX 2.3 Fast duration must be one of 6, 8, 10, 12, 14, 16, 18 or 20 seconds.")

    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.is_file() and target.stat().st_size > 100_000:
        return target

    image_uri = image_data_uri(reference_image) if reference_image is not None else None
    inputs = {
        "prompt": prompt,
        "duration": duration,
        "resolution": "1080p",
        "aspect_ratio": "16:9",
        "fps": 25,
        "camera_motion": camera if camera in {
            "dolly_in", "dolly_out", "dolly_left", "dolly_right",
            "jib_up", "jib_down", "static", "focus_shift", "none"
        } else "none",
        "generate_audio": False,
    }
    if image_uri:
        inputs["image"] = image_uri

    prediction = _request(API, token, method="POST", payload={"input": inputs}, prefer_wait=True)
    deadline = time.monotonic() + timeout_seconds
    while prediction.get("status") not in {"succeeded", "failed", "canceled"}:
        if time.monotonic() >= deadline:
            raise TimeoutError(f"Replicate video generation timed out. Prediction ID: {prediction.get('id')}")
        get_url = (prediction.get("urls") or {}).get("get")
        if not get_url:
            raise RuntimeError("Replicate returned a pending prediction without a polling URL.")
        time.sleep(poll_seconds)
        prediction = _request(get_url, token)

    if prediction.get("status") != "succeeded":
        raise RuntimeError(
            "LTX video generation failed: " + str(prediction.get("error") or prediction.get("logs") or prediction.get("status"))
        )

    output = prediction.get("output")
    if isinstance(output, list):
        output = output[0] if output else None
    if isinstance(output, dict):
        output = output.get("url")
    if not isinstance(output, str) or not output.startswith("https://"):
        raise RuntimeError(f"Replicate returned an unexpected video output: {output!r}")

    request = urllib.request.Request(output, headers={"User-Agent": "AI-Cinema-Engine/1.0"})
    with urllib.request.urlopen(request, timeout=180) as response:
        data = response.read()
    if len(data) < 100_000 or not data[:4] == b"\x00\x00\x00" and b"ftyp" not in data[:32]:
        raise RuntimeError("Replicate output did not look like a valid MP4 video.")
    target.write_bytes(data)
    return target
