"""Jinja template helpers.

Small formatting functions used across templates - kept here rather than in the
templates so the HTML stays readable.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any

from markupsafe import Markup, escape

from app.jobs import scoring


def register(app) -> None:
    app.jinja_env.filters["ago"] = ago
    app.jinja_env.filters["nice_date"] = nice_date
    app.jinja_env.filters["comp"] = comp_label
    app.jinja_env.filters["pct"] = percent
    app.jinja_env.filters["markdown"] = render_markdown
    app.jinja_env.filters["track"] = track_label
    app.jinja_env.globals["config"] = _template_config()


def _template_config() -> dict:
    import config as settings

    return {
        "COMP_FLOOR": settings.COMP_FLOOR,
        "COMP_TARGET": settings.COMP_TARGET,
        "NETWORKING_MIN": settings.NETWORKING_MIN_ACTIVE,
        "NETWORKING_MAX": settings.NETWORKING_MAX_ACTIVE,
        "QUESTIONS_PER_DAY": settings.QUESTIONS_PER_DAY,
        "FRESHNESS_DAYS": settings.FRESHNESS_DAYS,
    }


TRACK_LABELS = {
    "ai_native": "AI-native",
    "traditional_transformation": "Traditional / transformation",
    "pe_vc": "PE / VC",
    "consulting": "Consulting",
}


def track_label(value: Any) -> str:
    return TRACK_LABELS.get(value or "", "Unclassified")


def ago(value: Any) -> str:
    """'3 days ago' from an ISO timestamp."""
    if not value:
        return "-"
    try:
        stamp = datetime.fromisoformat(str(value))
    except ValueError:
        return str(value)
    if stamp.tzinfo is None:
        stamp = stamp.replace(tzinfo=timezone.utc)
    delta = datetime.now(timezone.utc) - stamp
    seconds = delta.total_seconds()
    if seconds < 90:
        return "just now"
    if seconds < 3600:
        return f"{int(seconds // 60)} min ago"
    if seconds < 86400:
        hours = int(seconds // 3600)
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    days = delta.days
    if days == 1:
        return "yesterday"
    if days < 30:
        return f"{days} days ago"
    months = days // 30
    return f"{months} month{'s' if months != 1 else ''} ago"


def nice_date(value: Any) -> str:
    if not value:
        return "-"
    try:
        return datetime.fromisoformat(str(value)).strftime("%d %b %Y")
    except ValueError:
        return str(value)


def comp_label(row: Any) -> str:
    """Pay range plus its confidence flag, which is always shown together."""
    data = dict(row) if not isinstance(row, dict) else row
    return scoring.comp_display(data)


def percent(value: Any, places: int = 0) -> str:
    try:
        return f"{float(value) * 100:.{places}f}%"
    except (TypeError, ValueError):
        return "-"


# ---------------------------------------------------------------------------
# A very small markdown renderer
# ---------------------------------------------------------------------------
# The primers are the only markdown in the app and they use a deliberately
# narrow subset: headings, paragraphs, bold, italic, inline code, bullet and
# numbered lists, and blockquotes. That is small enough to render here rather
# than take on a dependency, and everything is escaped before any tag is added.

_INLINE_PATTERNS = (
    (re.compile(r"\*\*(.+?)\*\*", re.S), r"<strong>\1</strong>"),
    (re.compile(r"(?<![\w*])\*([^*\n]+?)\*(?![\w*])"), r"<em>\1</em>"),
    (re.compile(r"`([^`]+?)`"), r"<code>\1</code>"),
)


def _inline(text: str) -> str:
    out = str(escape(text))
    for pattern, replacement in _INLINE_PATTERNS:
        out = pattern.sub(replacement, out)
    return out


def render_markdown(text: str) -> Markup:
    """Render the primer subset of markdown.

    Line-by-line, but with continuation handling: the primers wrap list items
    and blockquotes across several source lines, and each of those must join
    back into a single element rather than becoming separate blocks.
    """
    if not text:
        return Markup("")

    html: list[str] = []
    paragraph: list[str] = []
    quote: list[str] = []
    item: list[str] = []
    list_tag: str | None = None
    in_quote = False

    def flush_paragraph() -> None:
        nonlocal paragraph
        if paragraph:
            html.append(f"<p>{_inline(' '.join(paragraph))}</p>")
            paragraph = []

    def flush_item() -> None:
        nonlocal item
        if item:
            html.append(f"<li>{_inline(' '.join(item))}</li>")
            item = []

    def close_list() -> None:
        nonlocal list_tag
        flush_item()
        if list_tag:
            html.append(f"</{list_tag}>")
            list_tag = None

    def flush_quote() -> None:
        nonlocal quote
        if quote:
            html.append(f"<p>{_inline(' '.join(quote))}</p>")
            quote = []

    def close_quote() -> None:
        nonlocal in_quote
        if in_quote:
            flush_quote()
            html.append("</blockquote>")
            in_quote = False

    def close_all() -> None:
        flush_paragraph()
        close_list()
        close_quote()

    for raw_line in str(text).splitlines():
        stripped = raw_line.strip()

        # A blank line ends whatever block was open.
        if not stripped:
            close_all()
            continue

        heading = re.match(r"^(#{1,6})\s+(.*)$", stripped)
        if heading:
            close_all()
            level = min(len(heading.group(1)) + 1, 6)
            html.append(f"<h{level}>{_inline(heading.group(2))}</h{level}>")
            continue

        if stripped.startswith(">"):
            flush_paragraph()
            close_list()
            if not in_quote:
                html.append("<blockquote>")
                in_quote = True
            content = stripped[1:].lstrip()
            if content:
                quote.append(content)
            else:
                flush_quote()  # a bare ">" separates paragraphs inside a quote
            continue
        close_quote()

        bullet = re.match(r"^[-*]\s+(.*)$", stripped)
        numbered = re.match(r"^\d+[.)]\s+(.*)$", stripped)
        if bullet or numbered:
            flush_paragraph()
            wanted = "ul" if bullet else "ol"
            if list_tag != wanted:
                close_list()
                html.append(f"<{wanted}>")
                list_tag = wanted
            else:
                flush_item()
            item.append((bullet or numbered).group(1))
            continue

        # Not a new item, but a list is open: this is a wrapped continuation of
        # the current item, not a new paragraph.
        if list_tag and item:
            item.append(stripped)
            continue

        close_list()
        paragraph.append(stripped)

    close_all()
    return Markup("\n".join(html))
