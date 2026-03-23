from justdoit.fonts import FONTS
from justdoit.effects.color import colorize


def render(text: str, font: str = 'block', color: str = None, gap: int = 1) -> str:
    font_data = FONTS.get(font)
    if font_data is None:
        raise ValueError(f"Unknown font '{font}'. Available: {', '.join(FONTS.keys())}")

    text = text.upper()
    height = len(next(iter(font_data.values())))
    rows = [''] * height
    spacer = ' ' * gap

    for i, char in enumerate(text):
        glyph = font_data.get(char, font_data.get(' '))
        for row_idx, row in enumerate(glyph):
            if color:
                row = colorize(row, color, rainbow_index=i)
            rows[row_idx] += row + spacer

    return '\n'.join(rows)
