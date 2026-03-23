# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Run the CLI
python justdoit.py "Your Text"
python justdoit.py "FIRE" --color rainbow
python justdoit.py "hello" --font slim --color cyan
python justdoit.py "hi" --gap 3

# List available options
python justdoit.py --list-fonts
python justdoit.py --list-colors

# Optional: install globally
chmod +x justdoit.py && cp justdoit.py /usr/local/bin/justdoit
```

No external dependencies — pure Python 3 stdlib. No build step, no tests framework.

## Architecture

The entire CLI lives in a single file: `justdoit.py`.

**Data layer:** `FONTS` is a dict mapping font name → glyph dict. Each glyph is a list of strings (one per row). **All glyphs in a font must have the same height** — this is a hard constraint enforced by the row-concatenation logic in `render()`:
- `BLOCK`: 7-row font using Unicode block characters (`██`). Covers A-Z, 0-9, and common punctuation.
- `SLIM`: 3-row font using ASCII line-drawing characters.

**Rendering:** `render(text, font, color, gap)` uppercases input, iterates characters, looks up glyphs, and concatenates rows with a spacer. Unknown characters fall back to the space glyph. Returns the full multi-line string.

**Color:** `colorize(text, color, rainbow_index)` wraps text in ANSI escape codes. Rainbow mode cycles through `RAINBOW_CYCLE` (6 colors) per character index. Non-rainbow colors also apply bold (`\033[1m`).

**CLI:** `main()` uses `argparse`; font and color choices are validated against `FONTS` and `COLORS` dicts. The `rainbow` key in `COLORS` has a `None` value and is handled as a special case in `colorize()`.

## Skills Directory

`skills/ascii_art_generator/` is an OpenClaw skill wrapper. Its `main.py` calls `render()` from `justdoit.py` and writes the result to a file. It adds the repo root to `sys.path` so the import works regardless of working directory.

Note: the skill uses `--key=value` argument syntax (not `--key value`), which differs from the main CLI:

```bash
openclaw run skills/ascii_art_generator main.py --text='Hello World' --output=/path/to/output.txt
```
