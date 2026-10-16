from dataclasses import dataclass, field
from typing import List, Optional, Callable
from faster_whisper import WhisperModel


@dataclass
class Subtitle:
    index: int
    start: float  # seconds
    end: float    # seconds
    text: str


MODELS = ["tiny", "base", "small", "medium", "large-v2", "large-v3"]
LANGUAGES = {"日本語": "ja", "英語": "en", "自動検出": None}


def transcribe(
    audio_path: str,
    model_size: str = "medium",
    language: Optional[str] = "ja",
    progress_callback: Optional[Callable[[int, int], None]] = None,
) -> List[Subtitle]:
    model = WhisperModel(model_size, device="auto", compute_type="int8")
    segments, info = model.transcribe(audio_path, language=language, vad_filter=True)

    subtitles: List[Subtitle] = []
    total_duration = info.duration

    for seg in segments:
        idx = len(subtitles) + 1
        subtitles.append(Subtitle(index=idx, start=seg.start, end=seg.end, text=seg.text.strip()))
        if progress_callback and total_duration > 0:
            progress_callback(int(seg.end / total_duration * 100), 100)

    return subtitles
