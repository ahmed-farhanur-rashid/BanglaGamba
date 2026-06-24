"""
Download ~1B words of English from FineWeb (sample-10BT)
Streams and stops once word budget is hit — no need to download all 10BT.

Output: ./english_data/fineweb_en.jsonl
  {"text": "...", "source": "fineweb", "token_count": N}

Usage:
  pip install datasets tqdm
  python download_english.py
"""

import json
from pathlib import Path
from tqdm import tqdm

# ── Settings ──────────────────────────────────────────────────────────────────
WORD_BUDGET   = 1_000_000_000   # stop after ~1B words
OUTPUT_DIR    = Path("./english_data")
# ──────────────────────────────────────────────────────────────────────────────

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
OUT = OUTPUT_DIR / "fineweb_en.jsonl"


def download_fineweb():
    from datasets import load_dataset

    print("── Downloading FineWeb sample-10BT ──")
    print(f"   Word budget: {WORD_BUDGET:,}")
    print(f"   Streaming — will stop when budget is hit\n")

    ds = load_dataset(
        "HuggingFaceFW/fineweb",
        name="sample-10BT",
        split="train",
        streaming=True,
    )

    total_words = 0
    docs        = 0
    skipped     = 0

    with open(OUT, "w", encoding="utf-8") as f:
        for row in tqdm(ds, desc="FineWeb", unit=" docs"):
            text = (row.get("text") or "").strip()

            if not text:
                skipped += 1
                continue

            word_count = len(text.split())

            # Skip extremely short or long documents
            if word_count < 50 or word_count > 100_000:
                skipped += 1
                continue

            f.write(json.dumps(
                {"text": text, "source": "fineweb", "word_count": word_count},
                ensure_ascii=False
            ) + "\n")

            total_words += word_count
            docs        += 1

            if total_words >= WORD_BUDGET:
                print(f"\n   Budget reached.")
                break

    size_mb = OUT.stat().st_size / 1e6
    print(f"\nDone.")
    print(f"  Documents      : {docs:>12,}")
    print(f"  Words collected: {total_words:>12,}")
    print(f"  Skipped        : {skipped:>12,}")
    print(f"  Output         : {OUT}  ({size_mb:.1f} MB)")


if __name__ == "__main__":
    download_fineweb()
