"""
Hash-based deduplication for JSONL corpus files.

Removes exact and near-duplicate documents based on content hashing.
Processes one JSONL file at a time or an entire directory.

Usage:
    # Dedup a single file (in-place)
    python scripts/dedup_corpus.py saved/data/raw/cc_bangla/news_major.jsonl

    # Dedup entire directory (in-place, overwrites originals)
    python scripts/dedup_corpus.py saved/data/raw/cc_bangla/

    # Dry run — show stats without modifying files
    python scripts/dedup_corpus.py saved/data/raw/cc_bangla/ --dry-run
"""

import argparse
import hashlib
import json
import sys
from pathlib import Path


def content_hash(text: str) -> str:
    """SHA-256 hash of normalized text (stripped, lowercased)."""
    normalized = text.strip().lower()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def dedup_file(filepath: Path, dry_run: bool = False) -> dict:
    """Dedup a single JSONL file. Returns stats dict."""
    seen_hashes = set()
    kept = 0
    removed = 0
    lines = []

    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                doc = json.loads(line)
            except json.JSONDecodeError:
                continue

            h = content_hash(doc.get("text", ""))
            if h in seen_hashes:
                removed += 1
                continue
            seen_hashes.add(h)
            kept += 1
            lines.append(line)

    stats = {
        "file": str(filepath),
        "before": kept + removed,
        "after": kept,
        "removed": removed,
        "dup_ratio": f"{removed / (kept + removed) * 100:.1f}%" if (kept + removed) > 0 else "0%",
    }

    if not dry_run and removed > 0:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")

    return stats


def main():
    parser = argparse.ArgumentParser(description="Dedup JSONL corpus files")
    parser.add_argument("path", help="JSONL file or directory of JSONL files")
    parser.add_argument("--dry-run", action="store_true",
                         help="Show stats without modifying files")
    args = parser.parse_args()

    path = Path(args.path)
    if path.is_file():
        files = [path]
    elif path.is_dir():
        files = sorted(path.glob("*.jsonl"))
    else:
        print(f"Error: {path} not found", file=sys.stderr)
        sys.exit(1)

    if not files:
        print(f"No JSONL files found in {path}", file=sys.stderr)
        sys.exit(1)

    total_before = 0
    total_after = 0

    for f in files:
        stats = dedup_file(f, dry_run=args.dry_run)
        total_before += stats["before"]
        total_after += stats["after"]
        print(f"{stats['file']}: {stats['before']} -> {stats['after']} "
              f"({stats['removed']} removed, {stats['dup_ratio']} dup)")

    total_removed = total_before - total_after
    print(f"\nTotal: {total_before} -> {total_after} "
          f"({total_removed} removed, "
          f"{total_removed / total_before * 100:.1f}% dup)" if total_before > 0 else "")


if __name__ == "__main__":
    main()
