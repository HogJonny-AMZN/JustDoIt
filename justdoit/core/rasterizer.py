from justdoit.fonts import FONTS
from justdoit.effects.color import colorize
from justdoit.core.glyph import glyph_to_mask
from justdoit.effects.fill import density_fill, sdf_fill

_FILL_FNS = {
    'density': density_fill,
    'sdf': sdf_fill,
}


def render(text: str, font: str = 'block', color: str = None, gap: int = 1,
           fill: str = None) -> str:
    """Render text as ASCII art.

    fill: None (default block chars), 'density' (density-mapped ASCII),
          or 'sdf' (signed-distance-field shading).
    """
    font_data = FONTS.get(font)
    if font_data is None:
        raise ValueError(f"Unknown font '{font}'. Available: {', '.join(FONTS.keys())}")

    if fill is not None and fill not in _FILL_FNS:
        raise ValueError(f"Unknown fill '{fill}'. Available: {', '.join(_FILL_FNS.keys())}")

    text = text.upper()
    height = len(next(iter(font_data.values())))
    rows = [''] * height
    spacer = ' ' * gap

    fill_fn = _FILL_FNS.get(fill)

    for i, char in enumerate(text):
        glyph = font_data.get(char, font_data.get(' '))

        if fill_fn is not None:
            # Any non-space char counts as ink — works for block and slim fonts.
            ink = ''.join({ch for row in glyph for ch in row if ch != ' '}) or '█'
            mask = glyph_to_mask(glyph, ink_chars=ink)
            glyph = fill_fn(mask)

        for row_idx, row in enumerate(glyph):
            if color:
                row = colorize(row, color, rainbow_index=i)
            rows[row_idx] += row + spacer

    return '\n'.join(rows)
