from justdoit.core.glyph import mask_to_sdf

# Darkest to lightest — 12 levels.
DENSITY_CHARS = '@#S%?*+;:,. '


def density_fill(mask: list, density_chars: str = None) -> list:
    """Map mask float values to characters based on a density scale.

    1.0 → darkest char ('@'), 0.0 → space.
    Returns list of strings (same format as a font glyph).
    """
    chars = density_chars if density_chars is not None else DENSITY_CHARS
    n = len(chars)
    result = []
    for row in mask:
        line = ''
        for val in row:
            # val=1.0 → index 0 (darkest), val=0.0 → index n-1 (space)
            idx = int(val * (n - 1) + 0.5)
            idx = max(0, min(n - 1, idx))
            line += chars[n - 1 - idx]
        result.append(line)
    return result


def sdf_fill(mask: list, density_chars: str = None) -> list:
    """Fill using SDF — edge gets medium-density chars, interior dark, exterior space.

    Computes the signed distance field of the mask, then applies density_fill.
    Creates a natural shaded/outlined look.
    """
    sdf = mask_to_sdf(mask)
    return density_fill(sdf, density_chars)
