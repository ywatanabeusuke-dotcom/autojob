from dataclasses import dataclass
from pathlib import Path
from typing import List


@dataclass
class Scene:
    image_path: str
    text: str


def parse_script(script_path: str) -> List[Scene]:
    """Parse a manga-video script file into scenes.

    Format:
        IMAGE: panels/01.png
        TEXT: narration line 1
        narration line 2
        ---
        IMAGE: panels/02.png
        TEXT: ...
    """
    raw = Path(script_path).read_text(encoding="utf-8")
    scenes: List[Scene] = []

    image_path = None
    text_lines: List[str] = []
    in_text = False

    def flush():
        if image_path is not None:
            scenes.append(Scene(image_path=image_path, text="\n".join(text_lines).strip()))

    for raw_line in raw.splitlines():
        line = raw_line.rstrip()
        stripped = line.strip()

        if stripped == "---":
            flush()
            image_path = None
            text_lines = []
            in_text = False
            continue
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.upper().startswith("IMAGE:"):
            image_path = stripped.split(":", 1)[1].strip()
            in_text = False
            continue
        if stripped.upper().startswith("TEXT:"):
            text_lines.append(stripped.split(":", 1)[1].strip())
            in_text = True
            continue
        if in_text:
            text_lines.append(stripped)

    flush()

    for scene in scenes:
        if not scene.image_path or not scene.text:
            raise ValueError(f"Scene missing IMAGE or TEXT: {scene}")

    return scenes
