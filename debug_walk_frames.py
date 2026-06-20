"""
Debug script: dump each walk cycle frame as both ASCII text and a single PNG.
Run with: uv run python debug_walk_frames.py

Output goes to game/gallery/output/debug_frames/
  W01-f0.txt + W01-f0.png
  W01-f1.txt + W01-f1.png
  ...
"""
import re, sys, pathlib
sys.path.insert(0, '.')
sys.path.insert(0, 'game/gallery')

from generate_game_gallery import _walk_frames_start, _walk_frames_mid, _walk_frames_full
from justdoit.output.apng import frame_to_image

_ANSI_RE = re.compile(r"\033\[[0-9;]*m")

FONT_SIZE = 20
BG_COLOR  = "#111111"

out = pathlib.Path("game/gallery/output/debug_frames")
out.mkdir(parents=True, exist_ok=True)

walk_cycles = [
    ("W01", _walk_frames_start()),
    ("W02", _walk_frames_mid()),
    ("W03", _walk_frames_full()),
]

for prefix, frames in walk_cycles:
    for i, frame in enumerate(frames):
        stem = f"{prefix}-f{i}"

        # --- ASCII text ---
        plain = _ANSI_RE.sub("", frame)
        txt_path = out / f"{stem}.txt"
        txt_path.write_text(plain, encoding="utf-8")

        # --- Single PNG ---
        img = frame_to_image(frame, font_size=FONT_SIZE, bg_color=BG_COLOR)
        png_path = out / f"{stem}.png"
        img.save(png_path)

        sys.stdout.buffer.write(
            f"{stem}: {img.width}x{img.height}px  ascii={txt_path.name}\n".encode()
        )

sys.stdout.buffer.write(f"\nAll frames written to {out}\n".encode())
