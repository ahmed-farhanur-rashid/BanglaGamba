"""
Download BanglaNMT parallel Bangla-English pairs.
Downloads the tar.bz2 directly from HF Hub, extracts train.jsonl.
Writes as "bn |SEP| en" per line.

Usage:
  python scripts/download/01d_download_banglanmt.py
  python scripts/download/01d_download_banglanmt.py --max-docs 5000
"""

from __future__ import annotations

import argparse
import json
import tarfile
from pathlib import Path

from tqdm import tqdm
from _common import RAW_DIR, count_lines, write_doc, normalize_text, has_min_words


OUTPUT = RAW_DIR / "banglanmt_parallel.jsonl"
SOURCE = "banglanmt"
SOURCE_TYPE = "parallel_bn_en"
LANGUAGE_REGION = "EN_in_BN_context"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-docs", type=int, default=None,
                        help="Test mode: download at most N docs.")
    args = parser.parse_args()

    from huggingface_hub import hf_hub_download

    RAW_DIR.mkdir(parents=True, exist_ok=True)

    existing = count_lines(OUTPUT)
    if args.max_docs and existing >= args.max_docs:
        print(f"  \u21b7 banglanmt already complete ({existing:,} docs), skipping")
        return

    # Download tar.bz2 (133MB)
    print("[banglanmt] Downloading data/BanglaNMT.tar.bz2 from HF Hub...")
    tar_path = hf_hub_download(
        "csebuetnlp/BanglaNMT",
        "data/BanglaNMT.tar.bz2",
        repo_type="dataset",
    )
    print(f"[banglanmt] Downloaded to cache: {tar_path}")

    # Extract and process train.jsonl
    written = existing
    with tarfile.open(tar_path, "r:bz2") as tar:
        f = tar.extractfile("BanglaNMT/train.jsonl")
        total_lines = sum(1 for _ in f)
        f.seek(0)

        bar = tqdm(desc="BanglaNMT       ", unit="docs", unit_scale=True,
                   initial=existing, total=total_lines)
        for line in f:
            if existing > 0:
                existing -= 1
                bar.update(1)
                continue
            if args.max_docs and written >= args.max_docs:
                break

            row = json.loads(line)
            bn_text = row.get("bn", "")
            en_text = row.get("en", "")

            if len(bn_text.split()) < 5 or len(en_text.split()) < 5:
                bar.update(1)
                continue

            text = normalize_text(f"{bn_text} |SEP| {en_text}")
            if not has_min_words(text, min_words=10):
                bar.update(1)
                continue

            with open(OUTPUT, "a") as fout:
                write_doc(fout, text, SOURCE, SOURCE_TYPE, LANGUAGE_REGION)
            written += 1
            bar.update(1)
        bar.close()

    size_gb = OUTPUT.stat().st_size / (1024 ** 3)
    count = count_lines(OUTPUT)
    print(f"  \u2713 banglanmt \u2192 {OUTPUT}  ({count:,} docs, {size_gb:.1f} GB)")


if __name__ == "__main__":
    main()
