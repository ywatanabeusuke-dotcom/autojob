import tempfile
import unittest
from pathlib import Path

from manga_video.script import parse_script


class ParseScriptTest(unittest.TestCase):
    def test_parses_multiple_scenes(self):
        content = """
IMAGE: panels/01.png
TEXT: 昔々、ある村に
一人の少年が住んでいた。
---
IMAGE: panels/02.png
TEXT: その村には大きな森があった。
"""
        with tempfile.TemporaryDirectory() as tmp:
            script_path = Path(tmp) / "script.txt"
            script_path.write_text(content, encoding="utf-8")

            scenes = parse_script(str(script_path))

        self.assertEqual(len(scenes), 2)
        self.assertEqual(scenes[0].image_path, "panels/01.png")
        self.assertEqual(scenes[0].text, "昔々、ある村に\n一人の少年が住んでいた。")
        self.assertEqual(scenes[1].image_path, "panels/02.png")
        self.assertEqual(scenes[1].text, "その村には大きな森があった。")

    def test_rejects_scene_missing_text(self):
        content = "IMAGE: panels/01.png\n---\n"
        with tempfile.TemporaryDirectory() as tmp:
            script_path = Path(tmp) / "script.txt"
            script_path.write_text(content, encoding="utf-8")

            with self.assertRaises(ValueError):
                parse_script(str(script_path))


if __name__ == "__main__":
    unittest.main()
