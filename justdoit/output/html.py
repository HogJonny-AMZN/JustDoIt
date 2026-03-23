"""
Package: justdoit.output.html
HTML/CSS output target for rendered ASCII art (O01).

Wraps each colored character in a <span> with inline CSS color.
Output is a self-contained HTML snippet with a <pre> block on a dark background,
suitable for embedding in web pages or saving as a standalone .html file.

Pure Python stdlib — no external dependencies.
"""

import logging as _logging
from typing import Optional

from justdoit.output.ansi_parser import parse, effective_color

# -------------------------------------------------------------------------
# module global scope
_MODULE_NAME = "justdoit.output.html"
__updated__ = "2026-03-23 00:00:00"
__version__ = "0.1.0"
__author__ = ["jGalloway"]

_LOGGER = _logging.getLogger(_MODULE_NAME)

_HTML_HEADER = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>JustDoIt ASCII Art</title>
<style>
  body  {{ background: #111; margin: 0; padding: 1em; }}
  pre   {{ font-family: 'Courier New', Courier, monospace;
           font-size: 14px; line-height: 1.2; white-space: pre; }}
  span  {{ color: #ddd; }}
</style>
</head>
<body>
<pre>"""

_HTML_FOOTER = """</pre>
</body>
</html>"""


# -------------------------------------------------------------------------
def to_html(
    text: str,
    full_page: bool = True,
    bg_color: str = "#111111",
    font_size: int = 14,
) -> str:
    """Convert a rendered ANSI string to an HTML document or snippet.

    Each character is wrapped in a <span style="color: #rrggbb"> element.
    Consecutive characters sharing the same color are grouped into a single span.

    :param text: Multi-line rendered string from render() (with or without ANSI).
    :param full_page: If True, wrap in a complete HTML page; if False, return a <pre> snippet.
    :param bg_color: Background color for the page (default: '#111111').
    :param font_size: Font size in pixels for the <pre> block (default: 14).
    :returns: HTML string.
    """
    tokens = parse(text)

    # Group consecutive chars with the same color into single spans
    spans = []
    current_color: Optional[tuple] = None
    current_chars: list = []

    def _flush() -> None:
        if not current_chars:
            return
        r, g, b = effective_color(current_color)
        css = f"#{r:02x}{g:02x}{b:02x}"
        content = _html_escape("".join(current_chars))
        spans.append(f'<span style="color:{css}">{content}</span>')

    for ch, color in tokens:
        if ch == "\n":
            _flush()
            current_chars = []
            current_color = None
            spans.append("\n")
            continue
        if color != current_color:
            _flush()
            current_chars = []
            current_color = color
        current_chars.append(ch)
    _flush()

    body = "".join(spans)

    if not full_page:
        return f"<pre>{body}</pre>"

    header = _HTML_HEADER.format()
    # Inject custom bg and font-size
    header = header.replace(
        "background: #111",
        f"background: {bg_color}",
    ).replace(
        "font-size: 14px",
        f"font-size: {font_size}px",
    )
    return header + body + _HTML_FOOTER


# -------------------------------------------------------------------------
def save_html(text: str, path: str, **kwargs) -> None:
    """Save rendered ASCII art as an HTML file.

    :param text: Multi-line rendered string from render().
    :param path: Output file path (e.g. 'output.html').
    :param kwargs: Additional keyword arguments passed to to_html().
    """
    html = to_html(text, **kwargs)
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    _LOGGER.info(f"Saved HTML to {path}")


# -------------------------------------------------------------------------
def _html_escape(s: str) -> str:
    """Escape HTML special characters in a string.

    :param s: Input string.
    :returns: String with &, <, > escaped.
    """
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
