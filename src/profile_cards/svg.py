"""SVG building blocks shared by every panel: palette, fonts, frame, text, chips."""

from __future__ import annotations

import base64
import textwrap
import zlib
from pathlib import Path
from xml.sax.saxutils import escape

BG = "#07070f"
PANEL = "#0d0d1c"
PANEL_2 = "#12122a"
INK = "#e6e6f0"
DIM = "#8888a8"
DIMMER = "#555570"
CYAN = "#00f5ff"
MAGENTA = "#ff006e"
PURPLE = "#b537f2"
GREEN = "#06ffa5"
YELLOW = "#ffbe0b"
ACCENTS = (CYAN, MAGENTA, PURPLE, GREEN, YELLOW)

WIDTH = 900
# JetBrains Mono advances 600/1000 em per glyph, so mono text width is predictable.
MONO_ADVANCE = 0.6
# Orbitron is wide; this upper bound keeps titles from overflowing.
DISPLAY_ADVANCE = 0.86

FONT_FILES = (
    ("Orbitron", "orbitron-800.woff2"),
    ("JBMono", "jetbrainsmono-500.woff2"),
    ("NotoJP", "notosansjp-700.woff2"),
)


def font_css(fonts_dir: Path) -> str:
    """Fonts must be inlined: GitHub serves README SVGs as images, which can't fetch URLs."""
    rules = []
    for family, filename in FONT_FILES:
        data = base64.b64encode((fonts_dir / filename).read_bytes()).decode("ascii")
        rules.append(
            f"@font-face{{font-family:'{family}';"
            f"src:url(data:font/woff2;base64,{data}) format('woff2')}}"
        )
    return "".join(rules)


def image_data_uri(path: Path) -> str:
    mime = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg"}.get(
        path.suffix.lower()
    )
    if mime is None:
        raise ValueError(f"unsupported image type: {path.suffix}")
    return f"data:{mime};base64,{base64.b64encode(path.read_bytes()).decode('ascii')}"


def esc(value: str) -> str:
    return escape(value, {'"': "&quot;"})


def num(value: float) -> str:
    """Compact coordinates keep the files small and diffs readable."""
    text = f"{value:.1f}"
    return text[:-2] if text.endswith(".0") else text


def mono_width(text: str, size: float) -> float:
    return len(text) * size * MONO_ADVANCE


def fit_display(text: str, max_width: float, max_size: float) -> float:
    return min(max_size, max_width / max(1, len(text)) / DISPLAY_ADVANCE)


def wrap(text: str, width: int, max_lines: int | None = None) -> list[str]:
    lines = textwrap.wrap(text, width) or [""]
    if max_lines is not None and len(lines) > max_lines:
        lines = lines[:max_lines]
        lines[-1] = lines[-1][: width - 1].rstrip(" ,.;:") + "…"
    return lines


def text(
    x: float,
    y: float,
    content: str,
    *,
    cls: str = "m",
    size: float = 14,
    fill: str = INK,
    anchor: str = "start",
    extra: str = "",
) -> str:
    return (
        f'<text x="{num(x)}" y="{num(y)}" class="{cls}" font-size="{num(size)}" '
        f'fill="{fill}" text-anchor="{anchor}"{extra}>{esc(content)}</text>'
    )


def chip(
    x: float, y: float, label: str, color: str, *, size: float = 12, dot: bool = False
) -> tuple[str, float]:
    """Pill with a label; returns (svg, width) so callers can flow chips in a row."""
    pad = 10.0
    dot_space = 14.0 if dot else 0.0
    width = mono_width(label, size) + pad * 2 + dot_space
    height = size + 12
    parts = [
        f'<rect x="{num(x)}" y="{num(y)}" width="{num(width)}" height="{num(height)}" rx="{num(height / 2)}" '
        f'fill="{color}" fill-opacity=".08" stroke="{color}" stroke-opacity=".7"/>'
    ]
    if dot:
        parts.append(
            f'<circle class="pulse" cx="{num(x + pad + 3)}" cy="{num(y + height / 2)}" r="3.5" fill="{color}"/>'
        )
    parts.append(
        text(x + pad + dot_space, y + height / 2 + size * 0.36, label, size=size, fill=color)
    )
    return "".join(parts), width


def flow_chips(
    x: float, y: float, labels: tuple[str, ...], max_x: float, *, size: float = 12, gap: float = 8
) -> tuple[str, float]:
    """Lay chips left to right, wrapping at max_x. Returns (svg, bottom y)."""
    parts: list[str] = []
    cursor_x, cursor_y = x, y
    line_height = size + 12 + gap
    for i, label in enumerate(labels):
        width = mono_width(label, size) + 20
        if cursor_x + width > max_x and cursor_x > x:
            cursor_x, cursor_y = x, cursor_y + line_height
        svg, width = chip(cursor_x, cursor_y, label, ACCENTS[i % len(ACCENTS)], size=size)
        parts.append(svg)
        cursor_x += width + gap
    bottom = cursor_y + size + 12 if labels else y
    return "".join(parts), bottom


def header(kanji: str, title: str, tag: str, *, y: float = 46, width: float = WIDTH) -> str:
    return (
        f'<text x="28" y="{num(y)}">'
        f'<tspan class="j" font-size="20" fill="{MAGENTA}">{esc(kanji)}</tspan>'
        f'<tspan class="m" font-size="16" fill="{DIM}"> · </tspan>'
        f'<tspan class="d" font-size="17" fill="{CYAN}" letter-spacing="2">{esc(title)}</tspan>'
        f"</text>"
        + text(width - 28, y - 2, tag, size=11, fill=DIMMER, anchor="end")
        + f'<line x1="28" y1="{num(y + 14)}" x2="{num(width - 28)}" y2="{num(y + 14)}" '
        f'stroke="url(#edge)" stroke-opacity=".35"/>'
    )


# Frosted-glass fill. SVG-as-image has no backdrop-filter, so the "frost" comes from the
# blurred neon blobs painted behind every panel (see _blobs) showing through this tint.
GLASS = "url(#glass)"
GLASS_EDGE = "url(#glassedge)"


def glass(x: float, y: float, w: float, h: float, *, rx: float = 10, edge: str = GLASS_EDGE) -> str:
    """Translucent pane with a light rim and a specular line along the top edge."""
    return (
        f'<rect x="{num(x)}" y="{num(y)}" width="{num(w)}" height="{num(h)}" rx="{num(rx)}" '
        f'fill="{GLASS}" stroke="{edge}"/>'
        f'<path d="M{num(x + rx)} {num(y + 0.75)}H{num(x + w - rx)}" stroke="#ffffff" '
        f'stroke-opacity=".28"/>'
    )


def card(x: float, y: float, w: float, h: float, accent: str) -> str:
    return glass(x, y, w, h) + (
        f'<rect x="{num(x)}" y="{num(y + 12)}" width="3" height="{num(h - 24)}" rx="1.5" fill="{accent}"/>'
    )


_BLOB_LAYOUTS = (
    ((0.12, 0.2, CYAN), (0.88, 0.85, MAGENTA), (0.55, 0.0, PURPLE)),
    ((0.85, 0.1, PURPLE), (0.1, 0.9, CYAN), (0.5, 0.75, MAGENTA)),
    ((0.3, 1.0, MAGENTA), (0.75, 0.15, CYAN), (0.02, 0.3, PURPLE)),
)


def _blobs(width: float, height: float, seed: str) -> str:
    # crc32 instead of hash(): stable across runs, so unchanged panels produce no git diff.
    layout = _BLOB_LAYOUTS[zlib.crc32(seed.encode()) % len(_BLOB_LAYOUTS)]
    radius = max(90.0, min(height, 320.0) * 0.55)
    circles = "".join(
        f'<circle cx="{num(width * fx)}" cy="{num(height * fy)}" r="{num(radius)}" fill="{color}"/>'
        for fx, fy, color in layout
    )
    return f'<g filter="url(#soften)" opacity=".32">{circles}</g>'


_CSS = """
.d{{font-family:'Orbitron',sans-serif;font-weight:800}}
.m{{font-family:'JBMono',ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-weight:500}}
.j{{font-family:'NotoJP','Hiragino Sans','Yu Gothic',sans-serif;font-weight:700}}
@keyframes scan{{from{{transform:translateY(0)}}to{{transform:translateY({travel}px)}}}}
.scan{{animation:scan 7s linear infinite}}
@keyframes pulse{{0%,100%{{opacity:1}}50%{{opacity:.3}}}}
.pulse{{animation:pulse 2.2s ease-in-out infinite}}
@keyframes blink{{50%{{opacity:0}}}}
.blink{{animation:blink 1s steps(1) infinite}}
@keyframes spin{{to{{transform:rotate(360deg)}}}}
.spin{{transform-box:fill-box;transform-origin:center;animation:spin 30s linear infinite}}
@keyframes ga{{0%,90%,100%{{transform:translate(0,0);opacity:0}}91%{{transform:translate(-4px,1px);opacity:.85}}94%{{transform:translate(3px,-1px);opacity:.85}}97%{{transform:translate(-1px,0);opacity:.5}}}}
@keyframes gb{{0%,90%,100%{{transform:translate(0,0);opacity:0}}91%{{transform:translate(4px,-1px);opacity:.85}}94%{{transform:translate(-3px,1px);opacity:.85}}97%{{transform:translate(1px,0);opacity:.5}}}}
.ga{{animation:ga 5s steps(1) infinite}}
.gb{{animation:gb 5s steps(1) infinite}}
@media (prefers-reduced-motion:reduce){{*{{animation:none!important}}}}
"""


def document(width: float, height: float, title: str, body: str, fonts: str) -> str:
    w, h = num(width), num(height)
    corner = 16
    brackets = "".join(
        f'<path d="{d}" fill="none" stroke="{CYAN}" stroke-width="2" stroke-opacity=".8"/>'
        for d in (
            f"M8 {8 + corner}V8H{8 + corner}",
            f"M{num(width - 8 - corner)} 8H{num(width - 8)}V{8 + corner}",
            f"M8 {num(height - 8 - corner)}V{num(height - 8)}H{8 + corner}",
            f"M{num(width - 8 - corner)} {num(height - 8)}H{num(width - 8)}V{num(height - 8 - corner)}",
        )
    )
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
        f'viewBox="0 0 {w} {h}" role="img" aria-labelledby="title">'
        f'<title id="title">{esc(title)}</title>'
        f"<defs><style>{fonts}{_CSS.format(travel=num(height + 60))}</style>"
        f'<linearGradient id="edge" x1="0" y1="0" x2="1" y2="1">'
        f'<stop offset="0" stop-color="{CYAN}"/><stop offset=".5" stop-color="{PURPLE}"/>'
        f'<stop offset="1" stop-color="{MAGENTA}"/></linearGradient>'
        f'<linearGradient id="scanfade" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="{CYAN}" stop-opacity="0"/>'
        f'<stop offset="1" stop-color="{CYAN}" stop-opacity=".07"/></linearGradient>'
        f'<pattern id="grid" width="24" height="24" patternUnits="userSpaceOnUse">'
        f'<path d="M24 0H0V24" fill="none" stroke="{CYAN}" stroke-opacity=".05"/></pattern>'
        f'<clipPath id="frame"><rect width="{w}" height="{h}" rx="14"/></clipPath>'
        f'<filter id="soften" x="-50%" y="-50%" width="200%" height="200%">'
        f'<feGaussianBlur stdDeviation="52"/></filter>'
        f'<linearGradient id="glass" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="#ffffff" stop-opacity=".11"/>'
        f'<stop offset="1" stop-color="#ffffff" stop-opacity=".035"/></linearGradient>'
        f'<linearGradient id="glassedge" x1="0" y1="0" x2="1" y2="1">'
        f'<stop offset="0" stop-color="#ffffff" stop-opacity=".38"/>'
        f'<stop offset=".5" stop-color="#ffffff" stop-opacity=".06"/>'
        f'<stop offset="1" stop-color="#ffffff" stop-opacity=".18"/></linearGradient>'
        f"</defs>"
        f'<g clip-path="url(#frame)">'
        f'<rect width="{w}" height="{h}" fill="{BG}"/>'
        f"{_blobs(width, height, title)}"
        f'<rect width="{w}" height="{h}" fill="url(#grid)"/>'
        f"{body}"
        f'<rect class="scan" y="-60" width="{w}" height="60" fill="url(#scanfade)"/>'
        f"</g>"
        f'<rect x=".5" y=".5" width="{num(width - 1)}" height="{num(height - 1)}" rx="14" '
        f'fill="none" stroke="url(#edge)" stroke-opacity=".6"/>'
        f"{brackets}</svg>\n"
    )
