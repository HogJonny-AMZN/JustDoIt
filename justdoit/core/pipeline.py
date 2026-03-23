# Pipeline stage chaining — stub for Bite 2+.
#
# Future architecture:
#   text
#     → glyph lookup / generation
#     → rasterize to pixel grid
#     → spatial effects  (warp, distort, rotate, perspective)
#     → fill pass        (noise, gradient, pattern, cellular, fractal)
#     → composite layers (background, shadow, outline, glow)
#     → colorize         (flat, gradient, per-char, rainbow, palette)
#     → output target    (terminal, file, HTML, SVG, PNG)
