# Glyph representation.
#
# Current form: a list of strings, one per row. All glyphs in a font must
# have the same height — this invariant is relied on by the rasterizer.
#
# Future (Bite 2): abstract to a 2D boolean mask (list[list[bool]]) so that
# the ink cells can be filled with arbitrary characters, noise, gradients, etc.

# Type alias — documents intent without adding runtime cost.
Glyph = list  # list[str] today; will become list[list[bool]]
