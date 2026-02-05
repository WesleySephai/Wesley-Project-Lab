"""Download & render a coordinate-based secret message.

This script is resilient: it will use `requests` when available and fall back to
`urllib` when running in minimal environments. Use `--sample` to run an
offline example or `--test` to run the built-in self-check.
"""
from __future__ import annotations

import sys
from typing import List, Tuple

# graceful optional dependency
try:
    import requests  # type: ignore
    _HAS_REQUESTS = True
except Exception:
    import urllib.request
    _HAS_REQUESTS = False

# default URL (public, read-only)
DOC_URL = (
    "https://docs.google.com/document/d/e/2PACX-1vQiVT_Jj04V35C-YRzvoqyEYYzdXHcRyMUZCVQRYCu6gQJX7hbNhJ5eFCMuoX47cAsDW2ZBYppUQITr/pub"
)


def _fetch_text(url: str, timeout: float = 10.0) -> str:
    """Fetch a URL and return decoded text, using requests when available.

    Raises the same exceptions the underlying library would raise.
    """
    if _HAS_REQUESTS:
        resp = requests.get(url, timeout=timeout)
        resp.raise_for_status()
        return resp.text

    with urllib.request.urlopen(url, timeout=timeout) as r:
        return r.read().decode("utf-8")


def decode_secret_message_from_text(text: str) -> str:
    """Parse coordinate lines from `text` and render the message grid.

    Each non-empty line must be: "<char> <x> <y>". Lines that don't match are
    ignored. Returns the rendered multiline string (rows joined with "\n").
    """
    lines = [ln for ln in (l.strip() for l in text.splitlines()) if ln]

    coords: List[Tuple[str, int, int]] = []
    for line in lines:
        parts = line.split()
        if len(parts) != 3:
            continue
        char = parts[0]
        try:
            x = int(parts[1])
            y = int(parts[2])
        except ValueError:
            continue
        coords.append((char, x, y))

    if not coords:
        return ""

    max_x = max(x for _, x, _ in coords)
    max_y = max(y for _, _, y in coords)

    grid = [[" " for _ in range(max_x + 1)] for _ in range(max_y + 1)]
    for char, x, y in coords:
        grid[y][x] = char

    return "\n".join("".join(row) for row in grid)


def decode_secret_message(url: str) -> str:
    """Fetch `url` and decode the secret message.

    Separated so callers can test `decode_secret_message_from_text` independently.
    """
    text = _fetch_text(url)
    return decode_secret_message_from_text(text)


# --- small offline sample + self-test -------------------------------------------------
_SAMPLE = """H 0 0
E 1 0
L 2 0
L 3 0
O 4 0
W 0 1
O 1 1
R 2 1
L 3 1
D 4 1
"""
_SAMPLE_EXPECT = "HELLO\nWORLD"


def _self_test() -> None:
    out = decode_secret_message_from_text(_SAMPLE)
    assert out == _SAMPLE_EXPECT, f"self-test failed: {out!r} != {_SAMPLE_EXPECT!r}"


# --- CLI -----------------------------------------------------------------------------
if __name__ == "__main__":
    args = sys.argv[1:]
    if not args:
        # try network, otherwise fall back to sample
        try:
            print(decode_secret_message(DOC_URL))
        except Exception as exc:  # network or other runtime error
            print(f"⚠️  network fetch failed: {exc!s}\nUsing offline sample instead:\n", file=sys.stderr)
            print(decode_secret_message_from_text(_SAMPLE))
        sys.exit(0)

    cmd = args[0].lower()
    if cmd in {"--sample", "sample"}:
        print(decode_secret_message_from_text(_SAMPLE))
        sys.exit(0)
    if cmd in {"--test", "test"}:
        _self_test()
        print("✅ self-test passed")
        sys.exit(0)

    # if arg is an existing file, read it; otherwise treat as URL
    import os

    path = args[0]
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as fh:
            print(decode_secret_message_from_text(fh.read()))
        sys.exit(0)

    # otherwise treat as URL
    try:
        print(decode_secret_message(path))
    except Exception as exc:
        print(f"Error fetching/decoding '{path}': {exc}", file=sys.stderr)
        sys.exit(2)

