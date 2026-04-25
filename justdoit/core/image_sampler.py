"""
Package: justdoit.core.image_sampler
General-purpose image-to-ASCII converter using 6-zone shape matching.

Converts any PIL.Image to a 2D grid of (char, rgb) tuples by dividing the
image into a grid of cells and matching each cell's luminance pattern to
the nearest character in the prebuilt shape DB.

Requires Pillow.
"""

import logging as _logging
from typing import Optional

# -------------------------------------------------------------------------
# module global scope
_MODULE_NAME = "justdoit.core.image_sampler"
__updated__ = "2026-04-24 00:00:00"
__version__ = "1.0.0"
__author__ = ["jGalloway"]

_LOGGER = _logging.getLogger(_MODULE_NAME)

try:
    import numpy as np
    _NUMPY_AVAILABLE = True
except ImportError:
    _NUMPY_AVAILABLE = False


# -------------------------------------------------------------------------
def _cell_vector_numpy(
    gray_arr: "np.ndarray",
    r0: int, r1: int, c0: int, c1: int,
    cell_h: int, cell_w: int,
) -> list:
    """Compute 6-zone density vector from a grayscale numpy array block.

    :param gray_arr: 2D numpy array (H, W) with values 0-255.
    :param r0: Top row of cell in pixels.
    :param r1: Bottom row of cell in pixels.
    :param c0: Left column of cell in pixels.
    :param c1: Right column of cell in pixels.
    :param cell_h: Cell height in pixels.
    :param cell_w: Cell width in pixels.
    :returns: List of 6 floats in [0.0, 1.0].
    """
    block = gray_arr[r0:r1, c0:c1].astype(float)
    bh, bw = block.shape

    h2, h3, w2 = bh // 2, bh // 3, bw // 2

    def zone(rs: int, re: int, cs: int, ce: int) -> float:
        z = block[rs:re, cs:ce]
        if z.size == 0:
            return 0.0
        return float(z.mean() / 255.0)

    return [
        zone(0,  h2,    0,  w2),
        zone(0,  h2,    w2, bw),
        zone(h3, 2*h3,  0,  w2),
        zone(h3, 2*h3,  w2, bw),
        zone(h2, bh,    0,  w2),
        zone(h2, bh,    w2, bw),
    ]


# -------------------------------------------------------------------------
def _cell_vector_pure(
    gray_pixels: list,
    img_w: int,
    r0: int, r1: int, c0: int, c1: int,
    cell_h: int, cell_w: int,
) -> list:
    """Compute 6-zone density vector from grayscale pixel list (pure Python).

    :param gray_pixels: Flat list of grayscale pixel values (0-255).
    :param img_w: Image width in pixels.
    :param r0: Top row of cell in pixels.
    :param r1: Bottom row of cell in pixels.
    :param c0: Left column of cell in pixels.
    :param c1: Right column of cell in pixels.
    :param cell_h: Cell height in pixels.
    :param cell_w: Cell width in pixels.
    :returns: List of 6 floats in [0.0, 1.0].
    """
    bh = r1 - r0
    bw = c1 - c0
    h2, h3, w2 = bh // 2, bh // 3, bw // 2

    def zone(rs: int, re: int, cs: int, ce: int) -> float:
        total = 0
        count = 0
        for r in range(r0 + rs, r0 + re):
            for c in range(c0 + cs, c0 + ce):
                total += gray_pixels[r * img_w + c]
                count += 1
        return total / (count * 255.0) if count > 0 else 0.0

    return [
        zone(0,  h2,    0,  w2),
        zone(0,  h2,    w2, bw),
        zone(h3, 2*h3,  0,  w2),
        zone(h3, 2*h3,  w2, bw),
        zone(h2, bh,    0,  w2),
        zone(h2, bh,    w2, bw),
    ]


# -------------------------------------------------------------------------
def _cell_avg_rgb_numpy(
    rgb_arr: "np.ndarray",
    r0: int, r1: int, c0: int, c1: int,
) -> tuple:
    """Average RGB of a cell block using numpy.

    :param rgb_arr: 3D numpy array (H, W, 3).
    :param r0: Top row of cell in pixels.
    :param r1: Bottom row of cell in pixels.
    :param c0: Left column of cell in pixels.
    :param c1: Right column of cell in pixels.
    :returns: (r, g, b) tuple of ints 0-255.
    """
    block = rgb_arr[r0:r1, c0:c1]
    if block.size == 0:
        return (0, 0, 0)
    avg = block.mean(axis=(0, 1))
    return (int(avg[0]), int(avg[1]), int(avg[2]))


# -------------------------------------------------------------------------
def _cell_avg_rgb_pure(
    rgb_pixels: list,
    img_w: int,
    r0: int, r1: int, c0: int, c1: int,
) -> tuple:
    """Average RGB of a cell block (pure Python).

    :param rgb_pixels: Flat list of (r, g, b) tuples.
    :param img_w: Image width in pixels.
    :param r0: Top row of cell in pixels.
    :param r1: Bottom row of cell in pixels.
    :param c0: Left column of cell in pixels.
    :param c1: Right column of cell in pixels.
    :returns: (r, g, b) tuple of ints 0-255.
    """
    tr, tg, tb = 0, 0, 0
    count = 0
    for r in range(r0, r1):
        for c in range(c0, c1):
            idx = r * img_w + c
            pr, pg, pb = rgb_pixels[idx]
            tr += pr
            tg += pg
            tb += pb
            count += 1
    if count == 0:
        return (0, 0, 0)
    return (tr // count, tg // count, tb // count)


# -------------------------------------------------------------------------
def image_to_ascii(
    image: "PIL.Image.Image",
    cell_w: int,
    cell_h: int,
    charset: str = "",
    color: bool = True,
    db: Optional[dict] = None,
) -> list:
    """Convert a PIL image to a 2D grid of (char, rgb_or_None) cells.

    For each cell in the grid:
      - Compute 6-zone coverage vector from the cell's pixels
      - Match to nearest char in the shape DB
      - Average the RGB of all pixels in the cell (for color=True)

    Cell grid dimensions:
      cols = image.width // cell_w
      rows = image.height // cell_h
      (rightmost/bottom partial cells are discarded)

    :param image: PIL.Image in any mode; converted to RGB internally.
    :param cell_w: Cell width in pixels (monospace char width).
    :param cell_h: Cell height in pixels (monospace char height).
    :param charset: Characters to consider for matching (default: printable ASCII).
    :param color: If True, return RGB per cell; if False, return None for color.
    :param db: Optional pre-built char DB; built/cached if not provided.
    :returns: list[rows] of list[cols] of (char, (r,g,b) | None).
    :raises ImportError: If Pillow is not installed.
    """
    try:
        from PIL import Image  # noqa: F401
    except ImportError:
        raise ImportError(
            "image_to_ascii requires Pillow. Install with: uv add --dev Pillow"
        )

    from justdoit.core.char_db import get_char_db, nearest_char, PRINTABLE_ASCII

    if not charset:
        charset = PRINTABLE_ASCII

    if db is None:
        db = get_char_db(charset, cell_h, cell_w)

    # Convert to RGB for color averaging
    rgb_image = image.convert("RGB")
    # Convert to grayscale for zone vector computation
    gray_image = image.convert("L")

    img_w, img_h = image.size
    cols = img_w // cell_w
    rows = img_h // cell_h

    if cols == 0 or rows == 0:
        return []

    grid: list = []

    if _NUMPY_AVAILABLE:
        import numpy as np
        gray_arr = np.array(gray_image)
        rgb_arr = np.array(rgb_image) if color else None

        for row in range(rows):
            row_data: list = []
            r0 = row * cell_h
            r1 = r0 + cell_h
            for col in range(cols):
                c0 = col * cell_w
                c1 = c0 + cell_w
                vec = _cell_vector_numpy(gray_arr, r0, r1, c0, c1, cell_h, cell_w)
                ch = nearest_char(vec, db)
                rgb = _cell_avg_rgb_numpy(rgb_arr, r0, r1, c0, c1) if color else None
                row_data.append((ch, rgb))
            grid.append(row_data)
    else:
        gray_pixels = list(gray_image.tobytes())
        if color:
            raw = rgb_image.tobytes()
            rgb_pixels = [(raw[i], raw[i+1], raw[i+2]) for i in range(0, len(raw), 3)]
        else:
            rgb_pixels = None

        for row in range(rows):
            row_data = []
            r0 = row * cell_h
            r1 = r0 + cell_h
            for col in range(cols):
                c0 = col * cell_w
                c1 = c0 + cell_w
                vec = _cell_vector_pure(gray_pixels, img_w, r0, r1, c0, c1, cell_h, cell_w)
                ch = nearest_char(vec, db)
                rgb = _cell_avg_rgb_pure(rgb_pixels, img_w, r0, r1, c0, c1) if color else None
                row_data.append((ch, rgb))
            grid.append(row_data)

    _LOGGER.debug("image_to_ascii: %dx%d image -> %d cols x %d rows grid", img_w, img_h, cols, rows)
    return grid


# -------------------------------------------------------------------------
def image_to_ascii_fast(
    image: "PIL.Image.Image",
    cell_w: int,
    cell_h: int,
    charset: str = "",
    color: bool = True,
    db: Optional[dict] = None,
) -> list:
    """Fully-vectorized image-to-ASCII converter (numpy required).

    Identical contract to image_to_ascii() but uses numpy stride tricks and
    batch matrix distance to compute all cell vectors and nearest-char lookups
    in one pass.  10-50x faster than the cell-loop path for large grids.

    Falls back to image_to_ascii() if numpy is unavailable.

    :param image: PIL.Image in any mode; converted to RGB/L internally.
    :param cell_w: Cell width in pixels.
    :param cell_h: Cell height in pixels.
    :param charset: Characters to consider for matching.
    :param color: If True, return RGB per cell; if False, return None for color.
    :param db: Optional pre-built char DB.
    :returns: list[rows] of list[cols] of (char, (r,g,b) | None).
    """
    if not _NUMPY_AVAILABLE:
        return image_to_ascii(image, cell_w, cell_h, charset=charset, color=color, db=db)

    try:
        from PIL import Image  # noqa: F401
    except ImportError:
        raise ImportError("image_to_ascii_fast requires Pillow.")

    import numpy as np
    from numpy.lib.stride_tricks import as_strided
    from justdoit.core.char_db import get_char_db, PRINTABLE_ASCII

    if not charset:
        charset = PRINTABLE_ASCII
    if db is None:
        db = get_char_db(charset, cell_h, cell_w)

    rgb_image = image.convert("RGB")
    gray_image = image.convert("L")

    img_w, img_h = image.size
    cols = img_w // cell_w
    rows = img_h // cell_h

    if cols == 0 or rows == 0:
        return []

    # --- Vectorized zone-vector computation ---
    # Extract non-overlapping cell blocks using stride tricks: (rows, cols, cell_h, cell_w)
    gray_arr = np.array(gray_image, dtype=np.float32)
    h_s, w_s = gray_arr.strides
    blocks = as_strided(
        gray_arr,
        shape=(rows, cols, cell_h, cell_w),
        strides=(cell_h * h_s, cell_w * w_s, h_s, w_s),
    )

    h2, h3, w2 = cell_h // 2, cell_h // 3, cell_w // 2
    # 6 zones: (rows, cols) each
    z0 = blocks[:, :, 0:h2,    0:w2  ].mean(axis=(2, 3))
    z1 = blocks[:, :, 0:h2,    w2:   ].mean(axis=(2, 3))
    z2 = blocks[:, :, h3:2*h3, 0:w2  ].mean(axis=(2, 3))
    z3 = blocks[:, :, h3:2*h3, w2:   ].mean(axis=(2, 3))
    z4 = blocks[:, :, h2:,     0:w2  ].mean(axis=(2, 3))
    z5 = blocks[:, :, h2:,     w2:   ].mean(axis=(2, 3))

    vecs = np.stack([z0, z1, z2, z3, z4, z5], axis=-1) / 255.0  # (rows, cols, 6)
    flat_vecs = vecs.reshape(-1, 6).astype(np.float32)           # (N, 6)

    # --- Batch nearest-char lookup via matrix distance ---
    chars_list = list(db.keys())
    char_mat = np.array([db[c] for c in chars_list], dtype=np.float32)  # (M, 6)

    # L2 distance: ||a-b||^2 = ||a||^2 - 2*a.b + ||b||^2
    # Avoids materializing (N, M, 6) — only (N, M) intermediate
    vecs_sq  = np.sum(flat_vecs ** 2, axis=1, keepdims=True)  # (N, 1)
    chars_sq = np.sum(char_mat  ** 2, axis=1, keepdims=True)  # (M, 1)
    cross    = flat_vecs @ char_mat.T                          # (N, M)
    dists    = vecs_sq + chars_sq.T - 2.0 * cross             # (N, M)

    best_idx    = np.argmin(dists, axis=1)                     # (N,)
    chars_arr   = np.array(chars_list)
    result_chars = chars_arr[best_idx].reshape(rows, cols)     # (rows, cols)

    # --- Vectorized average RGB ---
    if color:
        rgb_arr = np.array(rgb_image, dtype=np.float32)        # (H, W, 3)
        rh_s, rw_s, rc_s = rgb_arr.strides
        rgb_blocks = as_strided(
            rgb_arr,
            shape=(rows, cols, cell_h, cell_w, 3),
            strides=(cell_h * rh_s, cell_w * rw_s, rh_s, rw_s, rc_s),
        )                                                        # (rows, cols, cell_h, cell_w, 3)
        avg_rgb = rgb_blocks.mean(axis=(2, 3)).astype(np.uint8) # (rows, cols, 3)
    else:
        avg_rgb = None

    # --- Assemble output grid ---
    grid: list = []
    for r in range(rows):
        row_data: list = []
        for c in range(cols):
            ch  = str(result_chars[r, c])
            rgb = (int(avg_rgb[r, c, 0]), int(avg_rgb[r, c, 1]), int(avg_rgb[r, c, 2])) if color else None
            row_data.append((ch, rgb))
        grid.append(row_data)

    _LOGGER.debug(
        "image_to_ascii_fast: %dx%d -> %dx%d grid (vectorized)",
        img_w, img_h, cols, rows,
    )
    return grid
