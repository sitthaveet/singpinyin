#!/usr/bin/env python3
"""Scrape song lyrics + pinyin from Smule arrangement pages.

Smule song pages (e.g. https://www.smule.com/song/.../<key>/arrangement) are
client-side React apps, so the HTML contains no lyrics. The lyrics are loaded
from a JSON API instead:

    https://www.smule.com/api/arrangement?key=<key>

That response has a ``lyrics_list`` field: one string per line. On "with pinyin"
arrangements each lyric line looks like ``如果雨之后 rúguǒ yǔ zhīhòu`` -- the
Chinese text, a space, then the pinyin. This script fetches that API, splits
each line into its Chinese and pinyin parts, and writes a JSON file per song.

Usage:
    python scrape.py <url-or-key> [<url-or-key> ...]
    python scrape.py --input urls.txt        # one url/key per line
    python scrape.py <url> --out-dir lyrics   # default out-dir: ./lyrics

Only the standard library is used -- no pip install required.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

API_URL = "https://www.smule.com/api/arrangement?key={key}"

# A normal browser User-Agent; the API rejects some default UAs.
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
)

# Arrangement keys look like "5291328_5291328" (digits, underscore, digits).
KEY_RE = re.compile(r"(\d+_\d+)")

# CJK Unicode blocks: Unified Ideographs, Extension A, and compatibility forms.
CJK_RE = re.compile(r"[㐀-鿿豈-﫿]")


def extract_key(text: str) -> str:
    """Pull the arrangement key out of a Smule URL or accept a bare key."""
    match = KEY_RE.search(text)
    if not match:
        raise ValueError(f"could not find an arrangement key in: {text!r}")
    return match.group(1)


def fetch_arrangement(key: str, timeout: int = 30) -> dict:
    """Fetch and decode the arrangement JSON for a given key."""
    request = urllib.request.Request(
        API_URL.format(key=key),
        headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def is_cjk(char: str) -> bool:
    return bool(CJK_RE.match(char))


def split_line(line: str) -> dict:
    """Split one lyric line into its Chinese and pinyin parts.

    Lyric lines are formatted as "<chinese> <pinyin>". The Chinese part is a
    run of CJK characters (plus any punctuation/spaces); the pinyin part starts
    at the first Latin letter. Lines with only one script -- section markers
    like "作词：吴易纬" or notes like "Thank you" -- come back with the other
    field empty and ``type`` set accordingly.
    """
    stripped = line.strip()
    if not stripped:
        return {"raw": line, "chinese": "", "pinyin": "", "type": "blank"}

    # The pinyin part begins at the first Latin (non-CJK) letter.
    split_at = None
    for index, char in enumerate(stripped):
        if char.isalpha() and not is_cjk(char):
            split_at = index
            break

    if split_at is None:
        chinese, pinyin = stripped, ""
    else:
        chinese, pinyin = stripped[:split_at].strip(), stripped[split_at:].strip()

    # A real lyric line is "<chinese> <pinyin>" where the pinyin half is pure
    # Latin. If the part after the split still has CJK in it, the line is mixed
    # text (e.g. credits like "作曲：Eric周兴哲") -- keep it whole, not a lyric.
    if pinyin and CJK_RE.search(pinyin):
        chinese, pinyin = stripped, ""

    if chinese and pinyin:
        line_type = "lyric"
    elif chinese:
        line_type = "chinese-only"
    else:
        line_type = "pinyin-only"

    return {"raw": line, "chinese": chinese, "pinyin": pinyin, "type": line_type}


def parse_song(data: dict) -> dict:
    """Turn a raw arrangement payload into a structured lyrics record."""
    lines = [split_line(line) for line in data.get("lyrics_list", [])]
    return {
        "key": data.get("key"),
        "title": data.get("title"),
        "artist": data.get("artist"),
        "arranger": (data.get("owner") or {}).get("handle"),
        "web_url": data.get("web_url"),
        "cover_url": data.get("cover_url"),
        "has_lyrics": data.get("lyrics", False),
        "line_count": len(lines),
        "lyric_line_count": sum(1 for line in lines if line["type"] == "lyric"),
        "lines": lines,
    }


def scrape(target: str) -> dict:
    """Scrape a single song given a URL or arrangement key."""
    key = extract_key(target)
    return parse_song(fetch_arrangement(key))


def read_targets(args: argparse.Namespace) -> list[str]:
    targets = list(args.targets)
    if args.input:
        text = Path(args.input).read_text(encoding="utf-8")
        targets += [ln.strip() for ln in text.splitlines() if ln.strip()]
    return targets


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Scrape lyrics + pinyin from Smule song pages.",
    )
    parser.add_argument(
        "targets",
        nargs="*",
        help="Smule song URLs or arrangement keys (e.g. 5291328_5291328).",
    )
    parser.add_argument(
        "--input",
        help="Path to a file with one URL/key per line.",
    )
    parser.add_argument(
        "--out-dir",
        default="lyrics",
        help="Directory to write <key>.json files into (default: ./lyrics).",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=1.0,
        help="Seconds to wait between requests (default: 1.0).",
    )
    args = parser.parse_args(argv)

    targets = read_targets(args)
    if not targets:
        parser.error("no targets given -- pass URLs/keys or --input FILE")

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    failures = 0
    for index, target in enumerate(targets):
        try:
            song = scrape(target)
        except (urllib.error.URLError, ValueError, json.JSONDecodeError) as exc:
            print(f"FAIL  {target}: {exc}", file=sys.stderr)
            failures += 1
            continue

        out_path = out_dir / f"{song['key']}.json"
        out_path.write_text(
            json.dumps(song, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(
            f"OK    {song['key']}  {song['lyric_line_count']} lyric lines"
            f"  -> {out_path}"
        )

        if args.delay and index < len(targets) - 1:
            time.sleep(args.delay)

    if failures:
        print(f"\n{failures} of {len(targets)} failed.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
