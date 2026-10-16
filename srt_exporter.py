from typing import List
import textwrap


def seconds_to_srt(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int(round((seconds % 1) * 1000))
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def apply_line_wrap(text: str, max_chars: int) -> str:
    if max_chars <= 0 or len(text) <= max_chars:
        return text
    lines = textwrap.wrap(text, width=max_chars, break_long_words=True)
    return "\n".join(lines)


def export_srt(subtitles, output_path: str, max_chars: int = 0) -> None:
    with open(output_path, "w", encoding="utf-8-sig") as f:
        for sub in subtitles:
            body = apply_line_wrap(sub.text, max_chars)
            f.write(f"{sub.index}\n")
            f.write(f"{seconds_to_srt(sub.start)} --> {seconds_to_srt(sub.end)}\n")
            f.write(f"{body}\n\n")
