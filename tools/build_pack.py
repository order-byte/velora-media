#!/usr/bin/env python3
"""Build the downloadable SFX pack.

Put sounds into category folders inside pack/<Pack Name>/, for example

    pack/Aminur Rex SFX Pack/01 Whooshes & Transitions/Aminur Rex - Whoosh.wav

then run

    python3 tools/build_pack.py

It writes, into downloads/:
  - <pack>.zip                  the full pack (every category + README.txt)
  - <pack> - <category>.zip     one zip per category
  - manifest.json               what the download page shows (names, counts, sizes)

Only the Python standard library is used.
"""
import json
import re
import sys
import wave
import zipfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PACK_DIR = ROOT / "pack"
OUT_DIR = ROOT / "downloads"
AUDIO = {".wav", ".mp3", ".m4a", ".aif", ".aiff", ".flac", ".ogg"}


def slug(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def seconds(path):
    if path.suffix.lower() != ".wav":
        return None
    try:
        with wave.open(str(path)) as w:
            return round(w.getnframes() / float(w.getframerate()), 2)
    except (wave.Error, EOFError):
        return None


def clean_category(name):
    """'01 Whooshes & Transitions' -> 'Whooshes & Transitions' (order prefix is only for sorting)."""
    return re.sub(r"^\d+\s*[-_.]?\s*", "", name)


def write_zip(target, entries):
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for src, arcname in entries:
            z.write(src, arcname)
    return target.stat().st_size


def main():
    packs = [p for p in sorted(PACK_DIR.iterdir()) if p.is_dir()] if PACK_DIR.exists() else []
    if len(packs) != 1:
        sys.exit(f"Expected exactly one pack folder inside {PACK_DIR}, found {len(packs)}.")
    pack = packs[0]
    name = pack.name
    OUT_DIR.mkdir(exist_ok=True)
    for old in OUT_DIR.glob("*.zip"):
        old.unlink()

    categories, all_entries = [], []
    for cat_dir in sorted(d for d in pack.iterdir() if d.is_dir()):
        files = sorted(f for f in cat_dir.rglob("*") if f.is_file() and f.suffix.lower() in AUDIO)
        if not files:
            continue
        entries = [(f, f"{name}/{f.relative_to(pack).as_posix()}") for f in files]
        all_entries += entries
        title = clean_category(cat_dir.name)
        zip_name = f"{slug(name)}--{slug(title)}.zip"
        size = write_zip(OUT_DIR / zip_name, entries)
        categories.append({
            "name": title,
            "url": f"downloads/{zip_name}",
            "bytes": size,
            "files": [{"name": f.stem, "type": f.suffix[1:].upper(), "seconds": seconds(f), "bytes": f.stat().st_size} for f in files],
        })

    if not categories:
        sys.exit(f"No audio files found in {pack}.")

    for extra in sorted(p for p in pack.iterdir() if p.is_file() and p.suffix.lower() in {".txt", ".pdf", ".md"}):
        all_entries.append((extra, f"{name}/{extra.name}"))
    full_name = f"{slug(name)}.zip"
    full_size = write_zip(OUT_DIR / full_name, all_entries)

    manifest = {
        "name": name,
        "built": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "totalFiles": sum(len(c["files"]) for c in categories),
        "full": {"url": f"downloads/{full_name}", "bytes": full_size},
        "categories": categories,
    }
    (OUT_DIR / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"{name}: {manifest['totalFiles']} sounds in {len(categories)} categories")
    for c in categories:
        print(f"  {c['name']:<28} {len(c['files']):>3} sounds  {c['bytes'] / 1024:>8.0f} KB")
    print(f"  full pack zip: {full_size / 1024:.0f} KB  ->  downloads/{full_name}")


if __name__ == "__main__":
    main()
