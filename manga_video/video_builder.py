from typing import List, Tuple
from moviepy import ImageClip, AudioFileClip, concatenate_videoclips

ZOOM_RATE = 0.04  # fraction of extra zoom applied over a scene's full duration


def _scene_clip(image_path: str, audio_path: str, target_height: int, zoom: bool):
    audio = AudioFileClip(audio_path)
    duration = audio.duration

    clip = ImageClip(image_path).with_duration(duration).resized(height=target_height)
    if zoom and duration > 0:
        clip = clip.resized(lambda t: 1 + ZOOM_RATE * (t / duration))
    return clip.with_audio(audio)


def build_video(
    scene_audio_pairs: List[Tuple[str, str]],
    output_path: str,
    target_height: int = 1080,
    zoom: bool = True,
    fps: int = 24,
) -> None:
    """scene_audio_pairs: list of (image_path, audio_path) in playback order."""
    clips = [
        _scene_clip(image_path, audio_path, target_height, zoom)
        for image_path, audio_path in scene_audio_pairs
    ]
    final = concatenate_videoclips(clips, method="compose")
    final.write_videofile(output_path, fps=fps, codec="libx264", audio_codec="aac")
    final.close()
    for clip in clips:
        clip.close()
