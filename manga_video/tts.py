import asyncio
import edge_tts

DEFAULT_VOICE = "ja-JP-NanamiNeural"


async def _synthesize_async(text: str, out_path: str, voice: str) -> None:
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(out_path)


def synthesize(text: str, out_path: str, voice: str = DEFAULT_VOICE) -> None:
    asyncio.run(_synthesize_async(text, out_path, voice))
