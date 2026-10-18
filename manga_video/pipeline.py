import argparse
import csv
from dataclasses import dataclass
from pathlib import Path
from typing import List

from moviepy import AudioFileClip

from srt_exporter import export_srt
from manga_video.script import parse_script
from manga_video.tts import synthesize, DEFAULT_VOICE
from manga_video.video_builder import build_video


@dataclass
class _TimedLine:
    index: int
    start: float
    end: float
    text: str


def _audio_duration(path: str) -> float:
    clip = AudioFileClip(path)
    duration = clip.duration
    clip.close()
    return duration


def _write_timeline_csv(path: str, rows: List[dict]) -> None:
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=["scene", "image_path", "audio_file", "start", "end", "duration", "text"])
        writer.writeheader()
        writer.writerows(rows)


def generate_assets(
    script_path: str,
    output_dir: str,
    voice: str = DEFAULT_VOICE,
) -> None:
    """Generate narration audio per scene + subtitles.srt + timeline.csv for manual
    assembly in a video editor (e.g. Premiere), where images come from ChatGPT/Gemini
    and BGM is added separately."""
    scenes = parse_script(script_path)
    if not scenes:
        raise ValueError(f"No scenes found in script: {script_path}")

    out_dir = Path(output_dir)
    audio_dir = out_dir / "audio"
    audio_dir.mkdir(parents=True, exist_ok=True)

    subtitles: List[_TimedLine] = []
    timeline_rows: List[dict] = []
    cursor = 0.0

    for i, scene in enumerate(scenes, start=1):
        audio_name = f"scene_{i:03d}.mp3"
        audio_path = audio_dir / audio_name
        synthesize(scene.text, str(audio_path), voice=voice)
        duration = _audio_duration(str(audio_path))

        subtitles.append(_TimedLine(index=i, start=cursor, end=cursor + duration, text=scene.text))
        timeline_rows.append(
            {
                "scene": i,
                "image_path": scene.image_path,
                "audio_file": f"audio/{audio_name}",
                "start": f"{cursor:.3f}",
                "end": f"{cursor + duration:.3f}",
                "duration": f"{duration:.3f}",
                "text": scene.text,
            }
        )
        cursor += duration

    export_srt(subtitles, str(out_dir / "subtitles.srt"))
    _write_timeline_csv(str(out_dir / "timeline.csv"), timeline_rows)


def render_preview_video(output_dir: str, preview_path: str, zoom: bool = True) -> None:
    """Optional rough-cut mp4 built from already-generated assets (generate_assets),
    using each scene's own image + narration audio. Useful to sanity-check pacing
    before the real edit in Premiere; not the final deliverable."""
    out_dir = Path(output_dir)
    timeline_path = out_dir / "timeline.csv"
    if not timeline_path.exists():
        raise FileNotFoundError(f"timeline.csv not found in {output_dir}; run generate_assets first")

    with open(timeline_path, encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))

    scene_audio_pairs = [(row["image_path"], str(out_dir / row["audio_file"])) for row in rows]
    build_video(scene_audio_pairs, preview_path, zoom=zoom)


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Generate narration audio + subtitles.srt + timeline.csv from a manga-video script, "
            "for manual assembly in Premiere (images from ChatGPT/Gemini, BGM from Gemini)."
        )
    )
    parser.add_argument("script", help="Path to the script file (see manga_video/script.py for format)")
    parser.add_argument("output_dir", help="Directory to write audio/, subtitles.srt and timeline.csv into")
    parser.add_argument("--voice", default=DEFAULT_VOICE, help=f"edge-tts voice name (default: {DEFAULT_VOICE})")
    parser.add_argument(
        "--preview-video",
        metavar="PATH",
        help="Also render a rough-cut mp4 preview (auto zoom, no BGM) at this path, for pacing checks only",
    )
    parser.add_argument("--no-zoom", action="store_true", help="Disable the Ken Burns zoom effect in the preview video")
    args = parser.parse_args()

    generate_assets(args.script, args.output_dir, voice=args.voice)

    if args.preview_video:
        render_preview_video(args.output_dir, args.preview_video, zoom=not args.no_zoom)


if __name__ == "__main__":
    main()
