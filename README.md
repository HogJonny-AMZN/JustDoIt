# JustDoIt 🔡

ASCII art generator with a CLI. Turns text into bold block letters — right in your terminal.

```
      ██  ██  ██  ██████   ██████  ████████     ██████    ██████      ████████   ██████
      ██  ██  ██  ██       ██          ██        ██   ██  ██    ██        ██      ██
      ████████  ██████    ████████  ██████       ██   ██  ██    ██        ██      ██████
      ██  ██  ██       ██          ██        ██   ██  ██    ██        ██          ██
      ██  ██  ██████   ██          ██         ██████    ██████         ██      ██████
```

## Usage

```bash
python justdoit.py "Your Text"
python justdoit.py "FIRE" --color rainbow
python justdoit.py "CO3DEX" --font block --color yellow
python justdoit.py "hello" --font slim --color cyan
```

## Options

| Flag | Short | Description |
|------|-------|-------------|
| `--font` | `-f` | Font style: `block` (default), `slim` |
| `--color` | `-c` | Color: `red`, `green`, `yellow`, `blue`, `magenta`, `cyan`, `white`, `bold`, `rainbow` |
| `--gap` | `-g` | Gap between characters (default: 1) |
| `--list-fonts` | | List available fonts |
| `--list-colors` | | List available colors |

## Fonts

- **block** — Classic bold block letters, 7 rows tall. Full A-Z, 0-9, punctuation.
- **slim** — Narrower ASCII style, 3 rows tall. Faster to read at a glance.

## Examples

```bash
# Default block font
python justdoit.py "Just Do It"

# Rainbow mode (because why not)
python justdoit.py "YOLO" --color rainbow

# Slim font in cyan
python justdoit.py "hello" --font slim --color cyan
```

## Install (optional)

```bash
chmod +x justdoit.py
cp justdoit.py /usr/local/bin/justdoit
justdoit "hello world"
```

No dependencies — pure Python 3 stdlib.
