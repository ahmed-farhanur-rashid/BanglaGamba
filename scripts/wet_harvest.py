"""
Fast Common Crawl WET harvester — bulk download with domain filtering.

WET files contain pre-extracted plaintext from CC. Much faster than
fetching individual WARC records: download WET files in parallel,
stream-parse, filter by domain allowlist, save matching docs.

Usage:
    # Quick test — download first 50 WET files, filter for BD domains
    python scripts/wet_harvest.py --out saved/data/raw/cc_bangla/ --max-files 50

    # Full harvest — all 100K WET files (takes hours, but fast)
    python scripts/wet_harvest.py --out saved/data/raw/cc_bangla/ --workers 32
"""

import argparse
import gzip
import io
import json
import re
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import requests
from tqdm import tqdm

CC_BASE = "https://data.commoncrawl.org"
BENGALI_RE = re.compile(r"[\u0980-\u09FF]")
LATIN_RE = re.compile(r"[a-zA-Z]")

# Domain allowlist — same as cc_bd_harvest.py
DOMAINS = [
    # news_major
    "prothomalo.com", "kalerkantho.com", "jugantor.com", "samakal.com",
    "ittefaq.com.bd", "bdnews24.com", "banglanews24.com", "jagonews24.com",
    "risingbd.com", "dhakapost.com", "somoynews.tv", "channelionline.com",
    "bd-pratidin.com", "amadershomoy.com", "independent24.com", "ntvbd.com",
    "jamunatv.com", "news24bd.tv", "ekushey-tv.com", "rtvbd.com",
    "dailystarbangla.com", "thefinancialexpress.com.bd",
    # news_mid
    "deshrupantor.com", "banglatribune.com", "kalbela.com", "manabzamin.com",
    "bhorerkagoj.com", "nayadiganta.com", "protidinersangbad.com",
    "ajkerpordomoy.com", "dailysangbad.com.bd", "dainandin.com",
    "shomoyeralo.com", "bd24live.com", "mzamin.com", "newsbangla24.com",
    "goshinews.com", "thebangladeshtoday.com", "barta24.com", "ekattor.tv",
    "nagoriknews.tv", "alcnews.com",
    # tabloid
    "blitzbd.com", "dhakatimes24.com", "khaborer-kagoj.com",
    "lalonmart.com", "banglaonline.com",
    # government
    "bangladesh.gov.bd", "bb.org.bd", "bbs.gov.bd", "nctb.gov.bd",
    "moedu.gov.bd", "mopa.gov.bd", "bdgovt.com",
    # reference
    "bn.banglapedia.org", "bn.wikipedia.org",
    # informal
    "somewhereinblog.net", "valoidea.com", "banglarsamaj.com",
]

# Build fast lookup set
DOMAIN_SET = set(DOMAINS)


def is_bangla(text: str, min_ratio: float = 0.6) -> bool:
    bengali = len(BENGALI_RE.findall(text))
    latin = len(LATIN_RE.findall(text))
    total = bengali + latin
    if total < 50:
        return False
    return (bengali / total) >= min_ratio


def url_matches_domain(url: str) -> str | None:
    """Check if a URL matches any domain in our allowlist. Returns domain or None."""
    url_lower = url.lower()
    for domain in DOMAIN_SET:
        if domain in url_lower:
            return domain
    return None


def parse_wet_content(wet_bytes: bytes) -> list[dict]:
    """Parse a WET file and return matching documents."""
    docs = []
    try:
        text = gzip.decompress(wet_bytes).decode("utf-8", errors="replace")
    except Exception:
        return docs

    # WET format: blocks separated by blank lines
    # Each block starts with "WARC/1.0" header, then WARC-Type, WARC-Target-URI, etc.
    blocks = text.split("\n\n")
    current_uri = None
    current_text = []

    for line in text.split("\n"):
        if line.startswith("WARC-Target-URI:"):
            current_uri = line.split(":", 1)[1].strip()
        elif line.startswith("Content-Length:"):
            continue
        elif line.strip() == "" and current_uri:
            # End of header, start of content
            continue
        elif line.startswith("WARC/"):
            # New record — save previous if valid
            if current_uri and current_text:
                content = "\n".join(current_text)
                domain = url_matches_domain(current_uri)
                if domain and len(content) >= 200 and is_bangla(content):
                    docs.append({
                        "domain": domain,
                        "url": current_uri,
                        "text": content,
                    })
            current_uri = None
            current_text = []
        elif not line.startswith("WARC-") and current_uri is not None:
            # Content line (after blank line separator in WET)
            current_text.append(line)

    # Don't forget last record
    if current_uri and current_text:
        content = "\n".join(current_text)
        domain = url_matches_domain(current_uri)
        if domain and len(content) >= 200 and is_bangla(content):
            docs.append({
                "domain": domain,
                "url": current_uri,
                "text": content,
            })

    return docs


def download_and_parse(wet_path: str, timeout: int = 60) -> list[dict]:
    """Download a WET file and extract matching docs."""
    url = f"{CC_BASE}/{wet_path}"
    try:
        resp = requests.get(url, timeout=timeout)
        if resp.status_code != 200:
            return []
        return parse_wet_content(resp.content)
    except Exception:
        return []


def main():
    parser = argparse.ArgumentParser(description="Fast WET harvester")
    parser.add_argument("--out", default="saved/data/raw/cc_bangla/")
    parser.add_argument("--crawl", default="CC-MAIN-2026-21")
    parser.add_argument("--max-files", type=int, default=None,
                         help="Max WET files to download (None = all)")
    parser.add_argument("--workers", type=int, default=32,
                         help="Parallel download threads")
    parser.add_argument("--timeout", type=int, default=60,
                         help="HTTP timeout per WET file in seconds")
    args = parser.parse_args()

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Fetch WET paths
    print(f"Fetching WET paths for {args.crawl} ...", flush=True)
    paths_url = f"https://data.commoncrawl.org/crawl-data/{args.crawl}/wet.paths.gz"
    resp = requests.get(paths_url, timeout=30)
    all_paths = gzip.decompress(resp.content).decode().strip().split("\n")
    print(f"Total WET files: {len(all_paths)}", flush=True)

    if args.max_files:
        paths = all_paths[:args.max_files]
        print(f"Downloading first {args.max_files} files", flush=True)
    else:
        paths = all_paths
        print(f"Downloading ALL {len(paths)} files", flush=True)

    # Output files — one per domain
    out_files = {}
    write_lock = threading.Lock()
    total_kept = 0
    total_failed = 0

    def flush_doc(doc):
        nonlocal total_kept
        domain = doc["domain"]
        with write_lock:
            if domain not in out_files:
                out_files[domain] = open(out_dir / f"{domain.replace('.', '_')}.jsonl",
                                         "w", encoding="utf-8")
            out_files[domain].write(json.dumps(doc, ensure_ascii=False) + "\n")
            total_kept += 1

    pbar = tqdm(total=len(paths), desc="WET files", unit="file", ncols=100)
    start_time = time.time()

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(download_and_parse, p, args.timeout): p for p in paths}
        for future in as_completed(futures):
            docs = future.result()
            for doc in docs:
                flush_doc(doc)
            pbar.update(1)
            pbar.set_postfix(kept=total_kept)

    pbar.close()
    elapsed = time.time() - start_time

    # Close all files
    for f in out_files.values():
        f.close()

    print(f"\n{'='*60}", flush=True)
    print(f"DONE in {elapsed:.0f}s ({elapsed/60:.1f} min)", flush=True)
    print(f"Total kept: {total_kept:,}", flush=True)
    print(f"Files saved: {len(out_files)}", flush=True)
    for domain, f in sorted(out_files.items()):
        fpath = out_dir / f"{domain.replace('.', '_')}.jsonl"
        lines = sum(1 for _ in open(fpath))
        print(f"  {domain}: {lines:,} docs", flush=True)


if __name__ == "__main__":
    main()
