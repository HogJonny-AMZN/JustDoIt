# Glyph representation.
#
# GlyphMask: a 2D grid of floats (0.0 = empty, 1.0 = full ink).
# glyph_to_mask: converts a list-of-strings glyph into a GlyphMask.
# mask_to_sdf: computes a signed distance field from a GlyphMask.

from collections import deque

# Type aliases — documents intent without runtime cost.
Glyph = list       # list[str]
GlyphMask = list   # list[list[float]]


def glyph_to_mask(glyph: list, ink_chars: str = '█') -> list:
    """Convert a list-of-strings glyph to a 2D float mask.

    Characters in ink_chars map to 1.0; spaces map to 0.0.
    Any other non-space character also maps to 1.0, so this works
    correctly for fonts that use line-drawing characters (slim font).
    """
    return [
        [0.0 if ch == ' ' else (1.0 if (ch in ink_chars or ink_chars == '') else 1.0)
         for ch in row]
        for row in glyph
    ]


def mask_to_sdf(mask: list) -> list:
    """Compute a signed distance field from a float mask.

    Values are normalized to 0.0–1.0:
      1.0 = deep interior (far from any edge)
      ~0.5 = at the glyph edge
      0.0 = deep exterior (far from any ink)

    Pure Python, no dependencies.
    """
    rows = len(mask)
    if rows == 0:
        return mask
    cols = len(mask[0]) if mask[0] else 0
    if cols == 0:
        return mask

    INF = float(rows + cols + 1)

    def bfs_distance(target_val: float) -> list:
        """BFS distance transform: distance from each cell to nearest cell == target_val."""
        dist = [[INF] * cols for _ in range(rows)]
        q = deque()
        for r in range(rows):
            for c in range(cols):
                if mask[r][c] == target_val:
                    dist[r][c] = 0.0
                    q.append((r, c))
        while q:
            r, c = q.popleft()
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                nr, nc = r + dr, c + dc
                if 0 <= nr < rows and 0 <= nc < cols and dist[nr][nc] == INF:
                    dist[nr][nc] = dist[r][c] + 1.0
                    q.append((nr, nc))
        return dist

    dist_to_empty = bfs_distance(0.0)
    dist_to_ink = bfs_distance(1.0)

    # Raw SDF: positive inside, negative outside
    raw = []
    for r in range(rows):
        row = []
        for c in range(cols):
            if mask[r][c] > 0.5:
                row.append(dist_to_empty[r][c])    # interior: +distance to edge
            else:
                row.append(-dist_to_ink[r][c])     # exterior: -distance to ink
        raw.append(row)

    # Normalize to 0.0–1.0
    all_vals = [v for row in raw for v in row]
    min_val = min(all_vals)
    max_val = max(all_vals)

    if max_val == min_val:
        return [[0.5] * cols for _ in range(rows)]

    span = max_val - min_val
    return [[(v - min_val) / span for v in row] for row in raw]
