"""
Corpus quality assessment for JSONL files.

Shows document counts, text length distributions, domain balance,
duplicate ratios, and samples random documents for manual inspection.

Usage:
    # Stats for a directory of JSONL files
    python scripts/corpus_stats.py saved/data/raw/cc_bangla/

    # Stats for a single file
    python scripts/corpus_stats.py saved/data/raw/cc_bangla/news_major.jsonl

    # Include random samples (5 per file)
    python scripts/corpus_stats.py saved/data/raw/cc_bangla/ --samples 5
"""

import argparse
import hashlib
import json
import random
import sys
from collections import Counter
from pathlib import Path


def analyze_file(filepath: Path, num_samples: int = 0) -> dict:
    """Analyze a single JSONL file and return stats."""
    doc_count = 0
    total_chars = 0
    total_words = 0
    lengths = []
    domains = Counter()
    timestamps = []
    seen_hashes = set()
    dup_count = 0
    samples = []

    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                doc = json.loads(line)
            except json.JSONDecodeError:
                continue

            text = doc.get("text", "")
            doc_count += 1
            char_len = len(text)
            word_len = len(text.split())
            total_chars += char_len
            total_words += word_len
            lengths.append(char_len)

            domains[doc.get("domain", "unknown")] += 1
            if doc.get("timestamp"):
                timestamps.append(doc["timestamp"])

            # Dedup check
            h = hashlib.sha256(text.strip().lower().encode("utf-8")).hexdigest()
            if h in seen_hashes:
                dup_count += 1
            seen_hashes.add(h)

            # Random sample
            if num_samples > 0 and len(samples) < num_samples:
                samples.append({
                    "domain": doc.get("domain"),
                    "url": doc.get("url"),
                    "chars": char_len,
                    "words": word_len,
                    "preview": text[:200] + "..." if len(text) > 200 else text,
                })

    if not lengths:
        return {"file": str(filepath), "error": "no valid documents"}

    lengths_sorted = sorted(lengths)
    n = len(lengths_sorted)

    return {
        "file": filepath.name,
        "documents": doc_count,
        "total_words": total_words,
        "total_chars": total_chars,
        "total_mb": total_chars / (1024 * 1024),
        "avg_words": total_words / doc_count,
        "median_chars": lengths_sorted[n // 2],
        "min_chars": lengths_sorted[0],
        "max_chars": lengths_sorted[-1],
        "p10_chars": lengths_sorted[int(n * 0.1)],
        "p90_chars": lengths_sorted[int(n * 0.9)],
        "unique_domains": len(domains),
        "top_domains": domains.most_common(10),
        "duplicates": dup_count,
        "dup_ratio": f"{dup_count / doc_count * 100:.1f}%" if doc_count > 0 else "0%",
        "samples": samples,
    }


def main():
    parser = argparse.ArgumentParser(description="Corpus quality stats")
    parser.add_argument("path", help="JSONL file or directory")
    parser.add_argument("--samples", type=int, default=0,
                         help="Number of random samples per file to show")
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

    grand_total_docs = 0
    grand_total_words = 0
    grand_total_dups = 0
    all_domains = Counter()

    for filepath in files:
        stats = analyze_file(filepath, num_samples=args.samples)
        if "error" in stats:
            print(f"\n{stats['file']}: {stats['error']}")
            continue

        grand_total_docs += stats["documents"]
        grand_total_words += stats["total_words"]
        grand_total_dups += stats["duplicates"]

        print(f"\n{'='*60}")
        print(f"  {stats['file']}")
        print(f"{'='*60}")
        print(f"  Documents:      {stats['documents']:,}")
        print(f"  Total words:    {stats['total_words']:,}")
        print(f"  Total size:     {stats['total_mb']:.1f} MB")
        print(f"  Avg words/doc:  {stats['avg_words']:.0f}")
        print(f"  Char length:    min={stats['min_chars']}, "
              f"p10={stats['p10_chars']}, med={stats['median_chars']}, "
              f"p90={stats['p90_chars']}, max={stats['max_chars']}")
        print(f"  Unique domains: {stats['unique_domains']}")
        print(f"  Duplicates:     {stats['duplicates']:,} ({stats['dup_ratio']})")

        print(f"\n  Top domains:")
        for domain, count in stats["top_domains"]:
            pct = count / stats["documents"] * 100
            print(f"    {domain:40s} {count:>8,} ({pct:.1f}%)")

        for domain, count in stats["top_domains"]:
            all_domains[domain] += count

        if stats["samples"]:
            print(f"\n  Random samples:")
            for i, s in enumerate(stats["samples"], 1):
                print(f"\n  [{i}] {s['domain']} | {s['words']} words | {s['url']}")
                print(f"      {s['preview'][:300]}")

    print(f"\n{'='*60}")
    print(f"  GRAND TOTAL")
    print(f"{'='*60}")
    print(f"  Documents:      {grand_total_docs:,}")
    print(f"  Total words:    {grand_total_words:,}")
    print(f"  Duplicates:     {grand_total_dups:,} "
          f"({grand_total_dups / grand_total_docs * 100:.1f}%)" if grand_total_docs > 0 else "")
    print(f"  Unique domains: {len(all_domains)}")
    print(f"\n  Top 15 domains (all files combined):")
    for domain, count in all_domains.most_common(15):
        pct = count / grand_total_docs * 100
        print(f"    {domain:40s} {count:>8,} ({pct:.1f}%)")


if __name__ == "__main__":
    main()
