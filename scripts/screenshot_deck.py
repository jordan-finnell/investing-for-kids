"""Screenshot every slide of deck/index.html at a chosen viewport size.

Useful for iterating on the deck's layout at the presenter's resolution
without needing to Alt-Tab to a browser.

    uv pip install playwright
    playwright install chromium
    python scripts/screenshot_deck.py --viewport 3560x1440

Outputs: /tmp/deck_shots/slide_{N}.png
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DECK_URL = (PROJECT_ROOT / "deck" / "index.html").as_uri()
NUM_SLIDES = 7  # 6 logical, but slide 4 has 2 subsections → 7 total


def parse_viewport(v: str) -> tuple[int, int]:
    w, h = v.lower().split("x")
    return int(w), int(h)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--viewport", default="3560x1440", help="e.g. 3560x1440")
    ap.add_argument("--out", default="/tmp/deck_shots", help="output directory")
    ap.add_argument("--slides", default=None, help="comma-separated slide indexes (default: all)")
    args = ap.parse_args()

    width, height = parse_viewport(args.viewport)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    slide_indexes = (
        [int(s) for s in args.slides.split(",")]
        if args.slides
        else list(range(NUM_SLIDES))
    )

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": width, "height": height})
        page = context.new_page()

        for idx in slide_indexes:
            page.goto(f"{DECK_URL}#/{idx}")
            # Give reveal.js + plotly time to render and settle
            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(800)
            out = out_dir / f"slide_{idx}.png"
            page.screenshot(path=str(out), full_page=False)
            print(f"  → {out}  ({width}x{height})", file=sys.stderr)

        browser.close()


if __name__ == "__main__":
    main()
