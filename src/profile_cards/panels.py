"""One function per README panel. Each returns a complete, standalone SVG document."""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, timedelta

from profile_cards import metrics
from profile_cards.config import Config, CrewItem, Status
from profile_cards.models import Profile
from profile_cards.svg import (
    ACCENTS,
    CYAN,
    DIM,
    DIMMER,
    GLASS,
    GREEN,
    INK,
    MAGENTA,
    PANEL_2,
    PURPLE,
    WIDTH,
    YELLOW,
    card,
    chip,
    document,
    esc,
    fit_display,
    flow_chips,
    header,
    image_data_uri,
    mono_width,
    num,
    text,
    wrap,
)

MONTHS = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")


@dataclass(frozen=True)
class Context:
    cfg: Config
    profile: Profile
    fonts: str
    today: date

    @property
    def avatar(self) -> str | None:
        path = self.cfg.identity.avatar
        return image_data_uri(path) if path else None


def _emblem(ctx: Context, cx: float, cy: float, r: float, clip_id: str) -> str:
    avatar = ctx.avatar
    if avatar:
        return (
            f'<clipPath id="{clip_id}"><circle cx="{num(cx)}" cy="{num(cy)}" r="{num(r)}"/></clipPath>'
            f'<image href="{avatar}" x="{num(cx - r)}" y="{num(cy - r)}" width="{num(2 * r)}" '
            f'height="{num(2 * r)}" preserveAspectRatio="xMidYMid slice" clip-path="url(#{clip_id})"/>'
            f'<circle cx="{num(cx)}" cy="{num(cy)}" r="{num(r)}" fill="none" stroke="url(#edge)" stroke-width="2"/>'
        )
    mono = ctx.cfg.identity.monogram
    return (
        f'<circle cx="{num(cx)}" cy="{num(cy)}" r="{num(r)}" fill="{GLASS}" stroke="url(#edge)" stroke-width="2"/>'
        + text(
            cx,
            cy + r * 0.24,
            mono,
            cls="d",
            size=fit_display(mono, r * 1.3, r * 0.72),
            fill="url(#edge)",
            anchor="middle",
        )
    )


def hero(ctx: Context) -> str:
    ident = ctx.cfg.identity
    height = 280
    cx, cy = 150.0, 140.0
    parts = [
        f'<circle class="spin" cx="{num(cx)}" cy="{num(cy)}" r="106" fill="none" stroke="url(#edge)" '
        f'stroke-width="2" stroke-dasharray="3 11"/>',
        f'<circle cx="{num(cx)}" cy="{num(cy)}" r="94" fill="none" stroke="{CYAN}" stroke-opacity=".22"/>',
        _emblem(ctx, cx, cy, 82, "hero-avatar"),
    ]

    x = 290.0
    parts.append(
        f'<text x="{num(x)}" y="74" class="m" font-size="13" fill="{GREEN}">// SYSTEM.ONLINE'
        f'<tspan class="blink">_</tspan></text>'
    )
    name_size = fit_display(ident.name, WIDTH - x - 40, 62)
    for cls, fill in (("ga", MAGENTA), ("gb", CYAN)):
        parts.append(
            text(
                x, 140, ident.name, cls=f"d {cls}", size=name_size, fill=fill, extra=' opacity="0"'
            )
        )
    parts.append(text(x, 140, ident.name, cls="d", size=name_size, fill=INK))
    role_size = min(19.0, (WIDTH - x - 40) / max(1, len(ident.role)) / 0.6)
    parts.append(text(x, 180, ident.role, size=role_size, fill=INK))

    chip_x = x
    for i, label in enumerate(ident.chips):
        color = (GREEN, CYAN, MAGENTA, PURPLE, YELLOW)[i % 5]
        svg, width = chip(chip_x, 202, label, color, dot=i == 0)
        parts.append(svg)
        chip_x += width + 10

    parts.append(text(WIDTH - 28, 36, f"@{ident.login}", size=12, fill=DIM, anchor="end"))
    parts.append(text(WIDTH - 28, height - 22, "NODE // MX-01", size=11, fill=DIMMER, anchor="end"))
    return document(WIDTH, height, f"{ident.name} — {ident.role}", "".join(parts), ctx.fonts)


def wanted(ctx: Context) -> str:
    ident, about = ctx.cfg.identity, ctx.cfg.about
    parts: list[str] = []

    # Poster (left)
    px, py, pw, ph = 28.0, 28.0, 312.0, 360.0
    pcx = px + pw / 2
    parts.append(
        f'<rect x="{num(px)}" y="{num(py)}" width="{num(pw)}" height="{num(ph)}" rx="6" '
        f'fill="{YELLOW}" fill-opacity=".07" stroke="{YELLOW}" stroke-width="2"/>'
        f'<rect x="{num(px + 8)}" y="{num(py + 8)}" width="{num(pw - 16)}" height="{num(ph - 16)}" rx="3" '
        f'fill="none" stroke="{YELLOW}" stroke-opacity=".35" stroke-dasharray="2 4"/>'
    )
    parts.append(
        text(
            pcx,
            py + 62,
            "WANTED",
            cls="d",
            size=44,
            fill=YELLOW,
            anchor="middle",
            extra=' letter-spacing="6"',
        )
    )
    bx, by, bw, bh = px + 28, py + 82, pw - 56, 150.0
    parts.append(
        f'<rect x="{num(bx)}" y="{num(by)}" width="{num(bw)}" height="{num(bh)}" fill="{GLASS}" '
        f'stroke="{YELLOW}" stroke-opacity=".6"/>'
    )
    parts.append(_emblem(ctx, pcx, by + bh / 2, 58, "wanted-avatar"))
    parts.append(
        f'<pattern id="lines" width="4" height="4" patternUnits="userSpaceOnUse">'
        f'<rect width="4" height="1" fill="{YELLOW}" fill-opacity=".06"/></pattern>'
        f'<rect x="{num(bx)}" y="{num(by)}" width="{num(bw)}" height="{num(bh)}" fill="url(#lines)"/>'
    )
    parts.append(
        text(
            pcx,
            by + bh + 30,
            "DEAD OR ALIVE",
            size=13,
            fill=YELLOW,
            anchor="middle",
            extra=' letter-spacing="3"',
        )
    )
    parts.append(
        text(
            pcx,
            by + bh + 62,
            f'{ident.name.rstrip(".")} "{ident.handle}"',
            cls="d",
            size=fit_display(ident.name + ident.handle, pw - 50, 20),
            fill=INK,
            anchor="middle",
        )
    )
    parts.append(text(bx, py + ph - 42, "BOUNTY", size=12, fill=DIM))
    parts.append(
        text(
            bx + bw,
            py + ph - 38,
            f"{ctx.profile.total_contributions:,}",
            cls="d",
            size=26,
            fill=YELLOW,
            anchor="end",
        )
    )
    parts.append(
        text(
            pcx, py + ph - 18, "contributions · last 12 months", size=11, fill=DIM, anchor="middle"
        )
    )

    # About (right)
    x = 372.0
    parts.append(
        f'<text x="{num(x)}" y="54"><tspan class="j" font-size="20" fill="{MAGENTA}">手配書</tspan>'
        f'<tspan class="m" font-size="16" fill="{DIM}"> · </tspan>'
        f'<tspan class="d" font-size="17" fill="{CYAN}" letter-spacing="2">WANTED</tspan></text>'
        f'<line x1="{num(x)}" y1="68" x2="{num(WIDTH - 28)}" y2="68" stroke="url(#edge)" '
        f'stroke-opacity=".35"/>'
    )
    y = 100.0
    parts.append(
        text(x, y, "WHO I AM", cls="d", size=13, fill=MAGENTA, extra=' letter-spacing="2"')
    )
    y += 26
    for line in wrap(about.who, 52):
        parts.append(text(x, y, line, size=14.5, fill=INK))
        y += 22
    y += 16
    parts.append(
        text(x, y, "RIGHT NOW", cls="d", size=13, fill=MAGENTA, extra=' letter-spacing="2"')
    )
    y += 26
    for i, item in enumerate(about.now):
        lines = wrap(item, 48)
        bullet = ACCENTS[i % len(ACCENTS)]
        parts.append(
            f'<text x="{num(x)}" y="{num(y)}" class="m" font-size="14" fill="{bullet}">▸</text>'
        )
        for line in lines:
            parts.append(text(x + 20, y, line, size=14, fill=INK))
            y += 21
        y += 4

    height = max(py + ph + 28, y + 16)
    return document(WIDTH, height, "Wanted poster and about", "".join(parts), ctx.fonts)


def record(ctx: Context) -> str:
    parts = [header("学生記録", "STUDENT RECORD", "// no self-ratings: each line points to work")]
    y = 78.0
    for i, item in enumerate(ctx.cfg.record):
        accent = ACCENTS[i % len(ACCENTS)]
        parts.append(card(28, y, WIDTH - 56, 66, accent))
        parts.append(
            text(
                48,
                y + 28,
                item.attribute.upper(),
                cls="d",
                size=15,
                fill=INK,
                extra=' letter-spacing="1"',
            )
        )
        parts.append(text(48, y + 50, item.stack, size=13, fill=DIM))
        parts.append(
            text(WIDTH - 48, y + 28, f"▸ {item.evidence}", size=13, fill=accent, anchor="end")
        )
        y += 76
    return document(WIDTH, y + 14, "Student record", "".join(parts), ctx.fonts)


def arsenal(ctx: Context) -> str:
    parts = [header("武器", "ARSENAL", "// tools I use in real projects")]
    y = 82.0
    for i, group in enumerate(ctx.cfg.arsenal):
        accent = ACCENTS[i % len(ACCENTS)]
        parts.append(
            text(
                48,
                y + 17,
                group.label.upper(),
                cls="d",
                size=12,
                fill=accent,
                extra=' letter-spacing="1"',
            )
        )
        svg, bottom = flow_chips(230, y, group.items, WIDTH - 40, size=13)
        parts.append(svg)
        y = bottom + 14
    return document(WIDTH, y + 14, "Arsenal", "".join(parts), ctx.fonts)


def slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def crew_header(ctx: Context) -> str:
    body = header("仲間", "THE CREW", "// public projects · click a card to open it", y=44)
    return document(WIDTH, 76, "The crew: public projects", body, ctx.fonts)


def crew_card(ctx: Context, index: int, item: CrewItem) -> str:
    width, height = 440.0, 214.0
    repo = ctx.profile.repo(item.repo)
    accent = ACCENTS[index % len(ACCENTS)]
    parts = [
        text(28, 40, f"[{index + 1:02d}]", size=13, fill=MAGENTA),
        text(
            28,
            72,
            item.title.upper(),
            cls="d",
            size=fit_display(item.title, 330, 20),
            fill=INK,
            extra=' letter-spacing="1"',
        ),
        f'<line x1="28" y1="86" x2="{num(width - 28)}" y2="86" stroke="{accent}" stroke-opacity=".4"/>',
    ]
    if repo is not None:
        parts.append(text(width - 28, 40, f"★ {repo.stars}", size=13, fill=YELLOW, anchor="end"))
    y = 110.0
    for line in wrap(item.mission, 50, max_lines=3):
        parts.append(text(28, y, line, size=13, fill=DIM))
        y += 19
    tags_svg, _ = flow_chips(28, height - 46, item.tags, width - 150, size=11, gap=6)
    parts.append(tags_svg)
    if repo is not None and repo.primary_language:
        color = repo.primary_color or PURPLE
        label = repo.primary_language
        lx = width - 28 - mono_width(label, 12)
        parts.append(
            f'<circle cx="{num(lx - 10)}" cy="{num(height - 38)}" r="5" fill="{color}"/>'
            + text(width - 28, height - 34, label, size=12, fill=INK, anchor="end")
        )
    return document(width, height, f"Project: {item.title}", "".join(parts), ctx.fonts)


def classified(ctx: Context) -> str:
    parts = [
        header("機密", "CLASSIFIED FILES", "// private for now · walkthrough on request"),
    ]
    y = 80.0
    for i, item in enumerate(ctx.cfg.classified):
        accent = ACCENTS[(i + 1) % len(ACCENTS)]
        lines = wrap(item.mission, 92, max_lines=3)
        h = 50 + len(lines) * 19 + 40
        parts.append(card(28, y, WIDTH - 56, h, accent))
        parts.append(
            text(
                48,
                y + 32,
                item.title.upper(),
                cls="d",
                size=16,
                fill=INK,
                extra=' letter-spacing="1"',
            )
        )
        sx, sy = WIDTH - 170, y + 14
        parts.append(
            f'<g transform="rotate(-6 {num(sx + 60)} {num(sy + 14)})" opacity=".85">'
            f'<rect x="{num(sx)}" y="{num(sy)}" width="124" height="28" rx="3" fill="none" '
            f'stroke="{MAGENTA}" stroke-width="2"/>'
            + text(
                sx + 62,
                sy + 19,
                "CLASSIFIED",
                cls="d",
                size=12,
                fill=MAGENTA,
                anchor="middle",
                extra=' letter-spacing="2"',
            )
            + "</g>"
        )
        ly = y + 58
        for line in lines:
            parts.append(text(48, ly, line, size=13, fill=DIM))
            ly += 19
        tags_svg, _ = flow_chips(48, ly - 4, item.tags, WIDTH - 60, size=11, gap=6)
        parts.append(tags_svg)
        y += h + 12
    return document(WIDTH, y + 6, "Classified projects", "".join(parts), ctx.fonts)


def power(ctx: Context) -> str:
    p = ctx.profile
    s = metrics.streaks(p.days, ctx.today)
    parts = [header("戦闘力", "POWER LEVEL", "// live · refreshed daily")]

    # Commit/PR totals undercount private work with fine-grained tokens, while the
    # calendar and repo list don't, so the tiles are built from those.
    active = sum(1 for d in p.days if d.count > 0)
    tiles = (
        ("CONTRIBUTIONS", f"{p.total_contributions:,}", "last 12 months", CYAN),
        ("ACTIVE DAYS", f"{active}", f"of the last {len(p.days)}", MAGENTA),
        ("REPOSITORIES", f"{len(p.repos)}", "built and owned", PURPLE),
        ("STREAK", f"{s.current}d", f"best {s.longest}d", GREEN),
    )
    for i, (label, value, sub, color) in enumerate(tiles):
        tx = 28 + (i % 2) * 206
        ty = 80 + (i // 2) * 106
        parts.append(
            f'<rect x="{num(tx)}" y="{num(ty)}" width="196" height="96" rx="10" fill="{GLASS}" '
            f'stroke="{color}" stroke-opacity=".35"/>'
        )
        parts.append(text(tx + 18, ty + 26, label, size=11, fill=DIM, extra=' letter-spacing="1"'))
        parts.append(
            text(tx + 18, ty + 64, value, cls="d", size=fit_display(value, 160, 30), fill=color)
        )
        parts.append(text(tx + 18, ty + 84, sub, size=11, fill=DIMMER))

    lx, lw = 460.0, WIDTH - 28 - 460
    parts.append(text(lx, 98, "TOP LANGUAGES", size=11, fill=DIM, extra=' letter-spacing="1"'))
    shares = metrics.top_languages(
        p.repos, ctx.cfg.stats.exclude_languages, ctx.cfg.stats.top_languages
    )
    if not shares:
        parts.append(text(lx, 130, "no language data yet", size=13, fill=DIMMER))
    else:
        parts.append(
            f'<clipPath id="bar"><rect x="{num(lx)}" y="110" width="{num(lw)}" height="12" rx="6"/></clipPath>'
            f'<rect x="{num(lx)}" y="110" width="{num(lw)}" height="12" rx="6" fill="{PANEL_2}"/>'
        )
        bar_x = lx
        segments = []
        for share in shares:
            seg_w = lw * share.share
            segments.append(
                f'<rect x="{num(bar_x)}" y="110" width="{num(seg_w)}" height="12" fill="{share.color}"/>'
            )
            bar_x += seg_w
        parts.append(f'<g clip-path="url(#bar)">{"".join(segments)}</g>')
        y = 152.0
        for share in shares:
            parts.append(
                f'<circle cx="{num(lx + 6)}" cy="{num(y - 5)}" r="5" fill="{share.color}"/>'
            )
            parts.append(text(lx + 20, y, share.name, size=13, fill=INK))
            parts.append(
                text(WIDTH - 28, y, f"{share.share * 100:.1f}%", size=13, fill=DIM, anchor="end")
            )
            y += 24
    return document(WIDTH, 306, "Power level: GitHub stats", "".join(parts), ctx.fonts)


def voyage(ctx: Context) -> str:
    days = sorted(ctx.profile.days, key=lambda d: d.day)
    parts = [header("航海日誌", "VOYAGE LOG", "// contribution calendar · live")]
    if not days:
        parts.append(text(28, 110, "no contributions recorded yet", size=13, fill=DIMMER))
        return document(WIDTH, 150, "Contribution calendar", "".join(parts), ctx.fonts)

    # GitHub weeks start on Sunday: column = week index, row = weekday.
    start = days[0].day - timedelta(days=(days[0].day.weekday() + 1) % 7)
    cols = (days[-1].day - start).days // 7 + 1
    x0, y0 = 64.0, 92.0
    step = min(15.0, (WIDTH - x0 - 28) / cols)
    cell = step - 3
    palette = (PANEL_2, "#0b4f60", "#00a6b5", PURPLE, MAGENTA)
    lv = metrics.levels([d.count for d in days])
    recent = ctx.today - timedelta(days=6)

    for label, row in (("Mon", 1), ("Wed", 3), ("Fri", 5)):
        parts.append(text(28, y0 + row * step + cell - 2, label, size=10, fill=DIMMER))

    last_month = None
    for col in range(cols):
        month = (start + timedelta(days=col * 7)).month
        if month != last_month and col < cols - 2:
            parts.append(text(x0 + col * step, y0 - 10, MONTHS[month - 1], size=10, fill=DIM))
        last_month = month

    cells = []
    for day, level in zip(days, lv, strict=True):
        offset = (day.day - start).days
        col, row = offset // 7, offset % 7
        pulse = ' class="pulse"' if day.day >= recent and day.count > 0 else ""
        cells.append(
            f'<rect{pulse} x="{num(x0 + col * step)}" y="{num(y0 + row * step)}" width="{num(cell)}" '
            f'height="{num(cell)}" rx="2" fill="{palette[level]}"><title>{esc(day.day.isoformat())}: '
            f"{day.count}</title></rect>"
        )
    parts.extend(cells)

    bottom = y0 + 7 * step + 22
    parts.append(
        text(
            28,
            bottom,
            f"{ctx.profile.total_contributions:,} contributions in the last year",
            size=12,
            fill=DIM,
        )
    )
    lx = WIDTH - 28 - 5 * 15 - 40
    parts.append(text(lx - 8, bottom, "less", size=10, fill=DIMMER, anchor="end"))
    for i, color in enumerate(palette):
        parts.append(
            f'<rect x="{num(lx + i * 15)}" y="{num(bottom - 10)}" width="12" height="12" rx="2" fill="{color}"/>'
        )
    parts.append(text(lx + 5 * 15 + 4, bottom, "more", size=10, fill=DIMMER))
    return document(WIDTH, bottom + 22, "Contribution calendar", "".join(parts), ctx.fonts)


_STATUS_STYLE: dict[Status, tuple[str, str, bool]] = {
    "ring": ("IN THE RING", GREEN, True),
    "sparring": ("SPARRING", YELLOW, True),
    "next": ("NEXT FIGHT", MAGENTA, False),
}


def training(ctx: Context) -> str:
    t = ctx.cfg.training
    parts = [header("特訓", "TRAINING LOG", "// round by round")]
    y = 92.0
    for line in wrap(f"“{t.quote}”", 96):
        parts.append(text(28, y, line, size=13, fill=DIM, extra=' font-style="italic"'))
        y += 19
    y += 8
    for i, rnd in enumerate(t.rounds):
        label, color, pulse = _STATUS_STYLE[rnd.status]
        parts.append(
            f'<rect x="28" y="{num(y)}" width="{num(WIDTH - 56)}" height="44" rx="8" fill="{GLASS}" '
            f'stroke="{color}" stroke-opacity=".25"/>'
        )
        parts.append(
            f'<rect x="40" y="{num(y + 10)}" width="96" height="24" rx="4" fill="none" '
            f'stroke="{MAGENTA}" stroke-opacity=".7"/>'
            + text(
                88,
                y + 27,
                f"ROUND {i + 1}",
                cls="d",
                size=11,
                fill=MAGENTA,
                anchor="middle",
                extra=' letter-spacing="1"',
            )
        )
        parts.append(text(156, y + 27, wrap(rnd.title, 62, max_lines=1)[0], size=14, fill=INK))
        pill, pill_w = chip(0, 0, label, color, size=11, dot=pulse)
        parts.append(
            f'<g transform="translate({num(WIDTH - 40 - pill_w)} {num(y + 9)})">{pill}</g>'
        )
        y += 52
    return document(WIDTH, y + 10, "Training log", "".join(parts), ctx.fonts)


def footer(ctx: Context) -> str:
    body = (
        f'<text x="{num(WIDTH / 2)}" y="48" class="m" font-size="15" fill="{CYAN}" '
        f'text-anchor="middle">&gt; connection_closed --- see you on the next island'
        f'<tspan class="blink" fill="{MAGENTA}">_</tspan></text>'
    )
    return document(WIDTH, 80, "Footer", body, ctx.fonts)


Panel = Callable[[Context], str]

STATIC_PANELS: dict[str, Panel] = {
    "hero.svg": hero,
    "wanted.svg": wanted,
    "record.svg": record,
    "arsenal.svg": arsenal,
    "crew.svg": crew_header,
    "classified.svg": classified,
    "power.svg": power,
    "voyage.svg": voyage,
    "training.svg": training,
    "footer.svg": footer,
}


def crew_filename(item: CrewItem) -> str:
    return f"crew-{slug(item.repo)}.svg"


CREW_START = "<!-- crew:start (generated from config.toml) -->"
CREW_END = "<!-- crew:end -->"


def crew_markdown(cfg: Config, out_dir: str) -> str:
    links = [
        f'<a href="https://github.com/{esc(cfg.identity.login)}/{esc(item.repo)}">'
        f'<img src="{out_dir}/{crew_filename(item)}" width="49%" alt="{esc(item.title)}"/></a>'
        for item in cfg.crew
    ]
    return "\n".join([CREW_START, '<p align="center">', *links, "</p>", CREW_END])


def inject_crew(readme: str, block: str) -> str:
    """Replace the marked crew block so README links never drift from config.toml."""
    start, end = readme.find(CREW_START), readme.find(CREW_END)
    if start == -1 or end == -1 or end < start:
        return readme
    return readme[:start] + block + readme[end + len(CREW_END) :]


def render_all(ctx: Context) -> dict[str, str]:
    files = {name: panel(ctx) for name, panel in STATIC_PANELS.items()}
    for i, item in enumerate(ctx.cfg.crew):
        files[crew_filename(item)] = crew_card(ctx, i, item)
    return files
