from __future__ import annotations

import os
import tempfile
from functools import lru_cache

from app.core.config import get_settings


@lru_cache(maxsize=1)
def _model():
    from faster_whisper import WhisperModel
    s = get_settings()
    return WhisperModel(
        s.whisper_model,
        device=s.whisper_device,
        compute_type=s.whisper_compute_type,
    )


def transcribe_file(data: bytes | str, suffix: str = ".mp4") -> tuple[str, list[dict]]:
    source_is_path = isinstance(data, str)
    if source_is_path:
        path = data
    else:
        fd, path = tempfile.mkstemp(suffix=suffix)
        os.close(fd)
    try:
        if not source_is_path:
            with open(path, "wb") as f:
                f.write(data)
        segments, info = _model().transcribe(
            path,
            vad_filter=True,
            beam_size=5,
        )
        rows = []
        text_parts = []
        for seg in segments:
            text = (seg.text or "").strip()
            if not text:
                continue
            text_parts.append(text)
            rows.append({
                "start_ms": int(seg.start * 1000),
                "end_ms": int(seg.end * 1000),
                "text": text,
            })
        return " ".join(text_parts).strip(), rows
    finally:
        try:
            if not source_is_path or os.path.basename(path).startswith("iarh-media-"):
                os.remove(path)
        except OSError:
            pass
