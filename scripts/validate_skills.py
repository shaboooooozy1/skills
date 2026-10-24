#!/usr/bin/env python3
"""Validate every skill and plugin manifest in this repo.

Runs the official skill-creator quick_validate on each skill, then adds repo house rules:
  - name matches folder, contains no reserved word ("claude", "anthropic")
  - description is third person (does not open with "Use", "I ", "You ", "This skill")
  - SKILL.md body under 500 lines, no README.md inside a skill folder
  - plugin.json and marketplace.json parse, and every marketplace source exists

Usage: python scripts/validate_skills.py [--only plugins]   (exit 1 on any failure)
"""
import argparse
import json
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "skills" / "skill-creator" / "scripts"))
from quick_validate import validate_skill  # noqa: E402

RESERVED = ("claude", "anthropic")
BAD_OPENERS = ("use ", "i ", "you ", "this skill")
# Upstream Anthropic skills predate some house rules. Check them with the official validator only.
UPSTREAM = ROOT / "skills"


def frontmatter(path):
    text = path.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n?(.*)$", text, re.S)
    return (yaml.safe_load(m.group(1)), m.group(2)) if m else ({}, text)


def house_rules(skill_dir):
    errs, warns = [], []
    try:
        fm, body = frontmatter(skill_dir / "SKILL.md")
    except yaml.YAMLError:
        return [], []  # the official validator already reports the parse error
    if not isinstance(fm, dict):
        return [], []
    name = str(fm.get("name", ""))
    desc = " ".join(str(fm.get("description", "")).split())
    if name != skill_dir.name:
        errs.append(f"name '{name}' does not match folder '{skill_dir.name}'")
    if any(w in name for w in RESERVED):
        errs.append(f"name '{name}' contains a reserved word")
    if desc.lower().startswith(BAD_OPENERS):
        errs.append("description should be third person (e.g. 'Drafts…', 'Builds…')")
    if "use when" not in desc.lower() and "use whenever" not in desc.lower():
        warns.append("description has no 'Use when…' trigger clause")
    if len(body.splitlines()) > 500:
        errs.append(f"SKILL.md body is {len(body.splitlines())} lines (max 500)")
    links = [str(f.relative_to(skill_dir)) for f in skill_dir.rglob("*") if f.is_symlink()]
    if links:
        errs.append(f"symlinks are not allowed in a skill: {', '.join(links)}")
    if (skill_dir / "README.md").exists():
        errs.append("README.md inside a skill folder; move it to repo level")
    meta = fm.get("metadata")
    if meta is not None and not isinstance(meta, dict):
        errs.append("metadata must be a mapping, e.g. metadata: {version: 1.0.0}")
        meta = {}
    if not (meta or {}).get("version"):
        warns.append("no metadata.version")
    return errs, warns


def linked_path(d):
    """First symlink among d and its parents up to (not including) the repo root, else None.
    A link anywhere on that path, e.g. plugins/p -> ../outside, would pull outside files in."""
    for p in [d, *d.parents]:
        if p == ROOT:
            return None
        if p.is_symlink():
            return p
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", choices=["plugins", "skills"], help="Limit to one tree")
    a = ap.parse_args()

    dirs = []
    if a.only in (None, "plugins"):
        dirs += sorted(p.parent for p in (ROOT / "plugins").glob("*/skills/*/SKILL.md"))
    if a.only in (None, "skills"):
        dirs += sorted(p.parent for p in UPSTREAM.glob("*/SKILL.md"))

    failed = 0
    for d in dirs:
        ok, msg = validate_skill(d)
        if d.parent == UPSTREAM:
            # stylistic house rules skip upstream skills, but the symlink ban applies everywhere
            links = [str(f.relative_to(d)) for f in d.rglob("*") if f.is_symlink()]
            errs, warns = ([f"symlinks are not allowed in a skill: {', '.join(links)}"] if links else []), []
        else:
            errs, warns = house_rules(d)
        link = linked_path(d / "SKILL.md")
        if link:
            errs.insert(0, f"{link.relative_to(ROOT)} is a symlink; plugin and skill folders must be real folders")
        if not ok:
            errs.insert(0, msg)
        rel = d.relative_to(ROOT)
        status = "FAIL" if errs else "ok  "
        print(f"{status} {rel}")
        for e in errs:
            print(f"     error: {e}")
        for w in warns:
            print(f"     warn:  {w}")
        failed += bool(errs)

    for pj in sorted((ROOT / "plugins").glob("*/.claude-plugin/plugin.json")):
        try:
            data = json.loads(pj.read_text())
            if data.get("name") != pj.parent.parent.name:
                print(f"FAIL {pj.relative_to(ROOT)}: name != folder")
                failed += 1
        except json.JSONDecodeError as e:
            print(f"FAIL {pj.relative_to(ROOT)}: {e}")
            failed += 1

    mp = ROOT / ".claude-plugin" / "marketplace.json"
    market = json.loads(mp.read_text())
    for plug in market.get("plugins", []):
        src = ROOT / plug["source"]
        if not src.exists():
            print(f"FAIL marketplace plugin '{plug['name']}': source {plug['source']} missing")
            failed += 1
        for s in plug.get("skills", []):
            if not (ROOT / s / "SKILL.md").exists():
                print(f"FAIL marketplace plugin '{plug['name']}': skill {s} missing")
                failed += 1

    print(f"\n{len(dirs)} skills checked, {failed} failure(s)")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
