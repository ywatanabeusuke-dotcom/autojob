import argparse
import tempfile
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


def run_pipeline(
    script_path: str,
    output_video: str,
    voice: str = DEFAULT_VOICE,
    zoom: bool = True,
    srt_only: bool = False,
) -> None:
    scenes = parse_script(script_path)
    if not scenes:
        raise ValueError(f"No scenes found in script: {script_path}")

    output_path = Path(output_video)
    srt_path = output_path.with_suffix(".srt")

    with tempfile.TemporaryDirectory(prefix="manga_video_") as tmp_dir:
        scene_audio_pairs = []
        subtitles: List[_TimedLine] = []
        cursor = 0.0

        for i, scene in enumerate(scenes, start=1):
            audio_path = str(Path(tmp_dir) / f"scene_{i:03d}.mp3")
            synthesize(scene.text, audio_path, voice=voice)
            duration = _audio_duration(audio_path)

            subtitles.append(
                _TimedLine(index=i, start=cursor, end=cursor + duration, text=scene.text)
            )
            scene_audio_pairs.append((scene.image_path, audio_path))
            cursor += duration

        export_srt(subtitles, str(srt_path))

        if not srt_only:
            build_video(scene_audio_pairs, str(output_path), zoom=zoom)


def main():
    parser = argparse.ArgumentParser(
        description="Build a narrated manga video (image + TTS narration + subtitles) from a script file."
    )
    parser.add_argument("script", help="Path to the script file (see manga_video/script.py for format)")
    parser.add_argument("output", help="Output video path, e.g. output.mp4")
    parser.add_argument("--voice", default=DEFAULT_VOICE, help=f"edge-tts voice name (default: {DEFAULT_VOICE})")
    parser.add_argument("--no-zoom", action="store_true", help="Disable the Ken Burns zoom effect")
    parser.add_argument("--srt-only", action="store_true", help="Only generate narration timing + .srt, skip video rendering")
    args = parser.parse_args()

    run_pipeline(
        args.script,
        args.output,
        voice=args.voice,
        zoom=not args.no_zoom,
        srt_only=args.srt_only,
    )


if __name__ == "__main__":
    main()
