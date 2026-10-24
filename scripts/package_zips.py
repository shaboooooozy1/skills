#!/usr/bin/env python3
"""Build one claude.ai-ready ZIP per skill under plugins/ into dist/.

Each ZIP has the skill folder at its root (my-skill/SKILL.md), which is what
Customize > Skills > Upload expects. Caches and OS junk are excluded.

Usage: python scripts/package_zips.py [--out dist]
"""
import argparse
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKIP_PARTS = {"__pycache__", ".DS_Store", "node_modules", ".pytest_cache"}
MAX_BYTES = 30 * 1024 * 1024  # API upload limit (uncompressed)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="dist")
    a = ap.parse_args()
    out = (ROOT / a.out).resolve()
    out.mkdir(exist_ok=True)
    for skill_md in sorted((ROOT / "plugins").glob("*/skills/*/SKILL.md")):
        d = skill_md.parent
        root = d.resolve()
        links = [f for f in d.rglob("*") if f.is_symlink()]
        if links:
            # A symlink could pull runner-local files (credentials, /proc) into a published ZIP.
            raise SystemExit(f"{d.name}: symlinks are not allowed in skills: "
                             + ", ".join(str(f.relative_to(d)) for f in links))
        files = [f for f in sorted(d.rglob("*"))
                 if f.is_file() and not f.is_symlink() and f.resolve().is_relative_to(root)
                 and not (set(f.parts) & SKIP_PARTS)]
        size = sum(f.stat().st_size for f in files)
        if size > MAX_BYTES:
            raise SystemExit(f"{d.name} is {size / 1e6:.1f} MB uncompressed, over the 30 MB limit")
        z = out / f"{d.name}.zip"
        with zipfile.ZipFile(z, "w", zipfile.ZIP_DEFLATED) as zf:
            for f in files:
                zf.write(f, Path(d.name) / f.relative_to(d))
        print(f"{z}  ({len(files)} files, {size / 1024:.0f} KB)")


if __name__ == "__main__":
    main()
