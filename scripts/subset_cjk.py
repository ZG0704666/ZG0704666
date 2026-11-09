"""Rebuild scripts/fonts/CJKSub.otf against the copy actually in generate.py.

The shipped CJKSub.otf is a subset covering only the ORIGINAL author's Chinese
text. Any new characters we introduce (e.g. 安卓, 替你操控手机) are missing from
it and render as blank gaps. This script scans generate.py for every CJK char
in use, then subsets a full Noto Sans SC font down to exactly those glyphs.

    python scripts/subset_cjk.py path/to/NotoSansSC.ttf

If the full font isn't present locally it is fetched from a CDN. Run this
whenever you change Chinese copy so newly-added characters are covered.
"""
from __future__ import annotations

import re
import sys
import urllib.request
from pathlib import Path

from fontTools import subset
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

FONTS = Path(__file__).with_name("fonts")
OUT = FONTS / "CJKSub.otf"
FULL_CACHE = Path(__file__).parent / ".notosanssc.ttf"
SRC_URL = "https://cdn.jsdelivr.net/gh/google/fonts@main/ofl/notosanssc/NotoSansSC%5Bwght%5D.ttf"

CJK = re.compile(r"[\u2e80-\u9fff\uff00-\uffef]")


def used_chars() -> set[str]:
    text = (Path(__file__).with_name("generate.py")).read_text(encoding="utf-8")
    return set(CJK.findall(text))


def resolve_full() -> Path:
    if FULL_CACHE.exists() and FULL_CACHE.stat().st_size > 1_000_000:
        return FULL_CACHE
    if len(sys.argv) > 1 and Path(sys.argv[1]).exists():
        return Path(sys.argv[1])
    print(f"fetching full Noto Sans SC -> {FULL_CACHE.name}")
    urllib.request.urlretrieve(SRC_URL, FULL_CACHE)
    return FULL_CACHE


def main() -> None:
    chars = used_chars()
    if not chars:
        raise SystemExit("no CJK characters found in generate.py")
    src = resolve_full()

    font = TTFont(src)
    # Pin the variable font to a single weight (medium) so the subset stays
    # small and renders identically everywhere, then subset to used glyphs.
    if "fvar" in font:
        font = instancer.instantiateVariableFont(font, {"wght": 500})
    subsetter = subset.Subsetter(options=subset.Options(desubroutinize=True))
    subsetter.populate(unicodes=[ord(c) for c in chars])
    subsetter.subset(font)
    # Noto Sans SC has TrueType outlines, so we keep the default (non-CFF) flavor.
    font.save(OUT)

    # verify every char survived
    cmap = TTFont(OUT).getBestCmap()
    missing = [c for c in chars if ord(c) not in cmap]
    size_kb = OUT.stat().st_size / 1024
    print(f"CJKSub.otf rebuilt: {len(chars)} chars, {size_kb:.0f} KB, missing {len(missing)}")
    if missing:
        print("MISSING:", "".join(sorted(missing)))


if __name__ == "__main__":
    main()
