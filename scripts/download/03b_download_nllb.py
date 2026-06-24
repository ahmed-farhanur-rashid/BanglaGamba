"""
Download NLLB (ben_Beng-eng_Latn) → JSONL

Output format (one JSON object per line):
  {"bn": "...", "en": "...", "source": "nllb", "laser_score": 1.23}

Usage:
  pip install datasets tqdm
  python download_nmt_datasets.py

Edit SETTINGS below before running.
"""

import json
from pathlib import Path
from tqdm import tqdm

# ── Settings ──────────────────────────────────────────────────────────────────
LASER_THRESHOLD = 1.06      # min LASER3 score; raise to 1.1 for stricter
MAX_PAIRS       = None      # set e.g. 20_000_000 to cap; None = keep all
OUTPUT_DIR      = Path("./nmt_data")
# ──────────────────────────────────────────────────────────────────────────────

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
OUT = OUTPUT_DIR / "nllb_bn_en.jsonl"


def download_nllb():
    from datasets import load_dataset

    print("── Downloading NLLB ben_Beng-eng_Latn ──")
    print(f"   Streaming from HuggingFace (no 400GB download)")
    print(f"   LASER threshold : {LASER_THRESHOLD}")
    print(f"   Cap             : {MAX_PAIRS or 'none'}")

    ds = load_dataset(
        "allenai/nllb",
        "ben_Beng-eng_Latn",
        split="train",
        streaming=True,
        trust_remote_code=True,
    )

    kept = skipped_laser = skipped_empty = 0

    with open(OUT, "w", encoding="utf-8") as f:
        for row in tqdm(ds, desc="NLLB", unit=" pairs"):
            t     = row["translation"]
            score = row.get("laser_score", 0.0)
            bn    = t.get("ben_Beng", "").strip()
            en    = t.get("eng_Latn", "").strip()

            if not bn or not en:
                skipped_empty += 1
                continue
            if score < LASER_THRESHOLD:
                skipped_laser += 1
                continue

            f.write(json.dumps(
                {"bn": bn, "en": en, "source": "nllb", "laser_score": round(score, 4)},
                ensure_ascii=False
            ) + "\n")
            kept += 1

            if MAX_PAIRS and kept >= MAX_PAIRS:
                print(f"\n   Cap reached at {MAX_PAIRS:,} pairs.")
                break

    size_mb = OUT.stat().st_size / 1e6
    print(f"\nDone.")
    print(f"  Kept           : {kept:>12,}")
    print(f"  Skipped (laser): {skipped_laser:>12,}")
    print(f"  Skipped (empty): {skipped_empty:>12,}")
    print(f"  Output         : {OUT}  ({size_mb:.1f} MB)")


if __name__ == "__main__":
    download_nllb()
