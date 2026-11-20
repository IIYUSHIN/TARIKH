"""Pure text redaction, kept apart from the Azure call so it can be tested and explained alone."""
from __future__ import annotations


def apply_redactions(text: str, spans: list[tuple[int, int, str]]) -> str:
    """Replace (offset, length, category) spans with [CATEGORY]; overlapping spans become one label."""
    merged: list[list] = []
    for offset, length, category in sorted(spans, key=lambda s: (s[0], -s[1])):
        end = offset + length
        if merged and offset < merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([offset, end, category])
    out, cursor = [], 0
    for start, end, category in merged:
        out.append(text[cursor:start])
        out.append(f"[{category.upper()}]")
        cursor = end
    out.append(text[cursor:])
    return "".join(out)
