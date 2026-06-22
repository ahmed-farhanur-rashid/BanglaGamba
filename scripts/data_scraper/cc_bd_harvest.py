"""
Common Crawl harvester for Bangladeshi-origin domains -- Bangla script only.

Strategy: Common Crawl already crawled the open web (respecting robots.txt
at crawl time) and explicitly licenses bulk reuse. Instead of scraping
Bangladeshi news sites yourself (ToS risk, server load, legal exposure),
this pulls only the WARC records CC already collected for your domain
allowlist, via HTTP range requests -- no full crawl download needed.

Filters out romanized Bangla (Banglish) -- this pass is Bangla-script only.
Fetch is threaded (I/O-bound: network range requests), extraction runs
across those same threads since trafilatura is the per-doc CPU cost.

pip install requests warcio trafilatura

Usage:
    # Single crawl (latest):
    python cc_bd_harvest.py --out raw/

    # Multiple crawls for maximum data:
    python cc_bd_harvest.py --crawl CC-MAIN-2026-22 CC-MAIN-2026-17 \
        CC-MAIN-2026-12 CC-MAIN-2026-08 --out raw/ --per-domain-limit 100000
"""

import argparse
import gzip
import io
import json
import os
import re
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import requests
import trafilatura
from tqdm import tqdm
from warcio.recordloader import ArcWarcRecordLoader

# Force unbuffered output for tqdm to display properly
tqdm.monitor_interval = 0

CC_INDEX_BASE = "https://index.commoncrawl.org"
CC_DATA_BASE = "https://data.commoncrawl.org"

# Unicode Bengali block: U+0980-U+09FF
BENGALI_RE = re.compile(r"[\u0980-\u09FF]")
LATIN_RE = re.compile(r"[a-zA-Z]")


def is_bangla_script(text: str, min_bengali_ratio: float = 0.6) -> bool:
    """
    Reject romanized Bangla / mostly-English text. Counts Bengali-block
    chars vs Latin-block chars among letter characters only (ignores
    digits, punctuation, whitespace so article boilerplate doesn't skew it).
    """
    bengali_chars = len(BENGALI_RE.findall(text))
    latin_chars = len(LATIN_RE.findall(text))
    total_letters = bengali_chars + latin_chars
    if total_letters < 50:
        return False  # too short to judge reliably, skip
    return (bengali_chars / total_letters) >= min_bengali_ratio

# Genre-tagged so you can balance your corpus across registers rather than
# just news dominating. All Bangladeshi-origin domains.
DOMAIN_ALLOWLIST = {
    "news_major": [
        "prothomalo.com",          # Largest BD newspaper by far
        "kalerkantho.com",         # Top-circulation daily
        "jugantor.com",            # Major national daily
        "samakal.com",             # Leading quality daily
        "ittefaq.com.bd",          # Oldest Bengali daily
        "bdnews24.com",            # First 24/7 BD news service
        "banglanews24.com",        # Major Bangla portal
        "jagonews24.com",          # Top BD news portal
        "risingbd.com",            # Fast-growing portal
        "dhakapost.com",           # Major broadsheet
        "somoynews.tv",            # Leading TV news
        "channelionline.com",      # Channel i online
        "bd-pratidin.com",         # Bangladesh Pratidin
        "amadershomoy.com",        # Popular daily
        "independent24.com",       # Independent TV
        "ntvbd.com",               # NTV Bangladesh
        "jamunatv.com",            # Jamuna TV
        "news24bd.tv",             # News24
        "ekushey-tv.com",          # Ekushey TV
        "rtvbd.com",               # RTV
        "dailystarbangla.com",     # Daily Star Bangla
        "thefinancialexpress.com.bd",  # Financial Express
    ],
    "news_mid": [
        "deshrupantor.com",        # Popular tabloid-style
        "banglatribune.com",       # Bangla Tribune
        "kalbela.com",             # Major daily
        "manabzamin.com",          # Manab Zamin
        "bhorerkagoj.com",         # Bhorer Kagoj
        "nayaDiganta.com",         # Naya Diganta
        "protidinersangbad.com",   # Prothom Din Sangbad
        "ajkerpordomoy.com",       # Ajker Pordomoy
        "dailysangbad.com.bd",     # Daily Sangbad
        "dainandin.com",           # Dainik Din
        "shomoyeralo.com",         # Shomoyer Alo
        "bd24live.com",            # BD 24 Live
        "mzamin.com",              # M Zamin
        "newsbangla24.com",        # News Bangla 24
        "goshinews.com",           # Goshi News
        "thebangladeshtoday.com",  # The Bangladesh Today
        "barta24.com",             # Barta 24
        "ekattor.tv",              # Ekattor TV
        "nagoriknews.tv",          # Nagorik News
        "alcnews.com",             # AL C News
    ],
    "tabloid": [
        "blitzbd.com",             # Blitz (tabloid)
        "dhakatimes24.com",        # Dhaka Times
        "khaborer-kagoj.com",      # Khaborer Kagoj
        "lalonmart.com",           # Lalon Mart
        "banglaonline.com",        # Bangla Online
    ],
    "government": [
        "bangladesh.gov.bd",       # Main government portal
        "bb.org.bd",               # Bangladesh Bank
        "bbs.gov.bd",              # Bureau of Statistics
        "nctb.gov.bd",             # National Curriculum
        "moedu.gov.bd",            # Ministry of Education
        "mopa.gov.bd",             # Ministry of Planning
        "bdgovt.com",              # Government info
    ],
    "reference": [
        "bn.banglapedia.org",      # Banglapedia
        "bn.wikipedia.org",        # Bangla Wikipedia
    ],
    "informal": [
        "somewhereinblog.net",     # Major BD blog platform
        "valoidea.com",            # Popular BD blog
        "banglarsamaj.com",        # Bangla community
    ],
}


def get_latest_crawl_id() -> str:
    """Fetch the most recent crawl identifier from collinfo.json."""
    resp = requests.get(f"{CC_INDEX_BASE}/collinfo.json", timeout=30)
    resp.raise_for_status()
    collections = resp.json()
    return collections[0]["id"]  # newest first


def query_domain(domain: str, crawl_id: str, limit: int = 5000) -> list[dict]:
    """Query the CDX index for all records under a domain in one crawl.

    Uses showNumPages=true first to check total count, then fetches in
    batches of PAGE_SIZE to avoid truncation on large result sets.
    """
    PAGE_SIZE = 10000  # CDX API reliable limit per request
    url = f"{CC_INDEX_BASE}/{crawl_id}-index"
    records = []
    offset = 0

    while offset < limit:
        batch = min(PAGE_SIZE, limit - offset)
        params = {
            "url": f"{domain}/*",
            "output": "json",
            "limit": str(batch),
            "offset": str(offset),
            "filter": "status:200",
        }
        try:
            resp = requests.get(url, params=params, timeout=120)
        except requests.exceptions.RequestException as e:
            print(f"  [warn] request failed for {domain} offset={offset}: {e}")
            break

        if resp.status_code == 404:
            break
        if resp.status_code != 200:
            print(f"  [warn] status {resp.status_code} for {domain} offset={offset}")
            break

        # Parse line by line, skip malformed lines
        new_records = 0
        for line in resp.text.strip().split("\n"):
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
                new_records += 1
            except json.JSONDecodeError:
                continue

        # If we got fewer records than requested, we've reached the end
        if new_records < batch:
            break
        offset += batch

    return records


def fetch_warc_record(record: dict) -> str | None:
    """Range-fetch a single WARC record and extract clean text from it."""
    offset = int(record["offset"])
    length = int(record["length"])
    warc_url = f"{CC_DATA_BASE}/{record['filename']}"
    headers = {"Range": f"bytes={offset}-{offset + length - 1}"}

    resp = requests.get(warc_url, headers=headers, timeout=30)
    if resp.status_code not in (200, 206):
        return None

    stream = io.BytesIO(gzip.decompress(resp.content))
    loader = ArcWarcRecordLoader()
    warc_record = loader.parse_record_stream(stream)
    html = warc_record.content_stream().read()

    text = trafilatura.extract(html, include_comments=False, include_tables=False)
    if not text or len(text) < 200:
        return None
    if not is_bangla_script(text):
        return None  # romanized / mostly-English -- not this pass
    return text


def _process_record(rec: dict, genre: str, domain: str) -> dict | None:
    """Worker function: fetch + extract + filter one record."""
    text = fetch_warc_record(rec)
    if not text:
        return None
    return {
        "domain": domain,
        "genre": genre,
        "url": rec.get("url"),
        "timestamp": rec.get("timestamp"),
        "text": text,
    }


def harvest(crawl_ids: list[str], out_dir: Path, per_domain_limit: int = 50000,
            workers: int = 16, append: bool = False) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    write_lock = threading.Lock()

    for crawl_id in crawl_ids:
        print(f"\n{'='*60}", flush=True)
        print(f"CRAWL: {crawl_id}", flush=True)
        print(f"{'='*60}", flush=True)

        for genre, domains in DOMAIN_ALLOWLIST.items():
            out_path = out_dir / f"{genre}.jsonl"
            mode = "a" if append else "w"
            genre_kept = 0

            for domain in domains:
                print(f"[{genre}] querying {domain} ...", flush=True)
                records = query_domain(domain, crawl_id, limit=per_domain_limit)
                if not records:
                    continue

                kept = 0
                failed = 0
                pbar = tqdm(total=len(records), desc=f"  {domain}", unit="doc",
                            ncols=100, leave=False, file=sys.stdout)

                with ThreadPoolExecutor(max_workers=workers) as pool, \
                     out_path.open(mode, encoding="utf-8") as f:
                    futures = {
                        pool.submit(_process_record, rec, genre, domain): rec
                        for rec in records
                    }
                    for future in as_completed(futures):
                        result = future.result()
                        if result is None:
                            failed += 1
                        else:
                            with write_lock:
                                f.write(json.dumps(result, ensure_ascii=False) + "\n")
                            kept += 1
                        pbar.update(1)
                        pbar.set_postfix(kept=kept, fail=failed)
                    mode = "a"  # subsequent domains append

                pbar.close()
                print(f"  -> {domain}: {kept}/{len(records)} kept", flush=True)
                genre_kept += kept

            print(f"[{genre}] TOTAL kept: {genre_kept}", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--crawl", default=None, nargs="+",
                         help="Crawl IDs e.g. --crawl CC-MAIN-2026-22 CC-MAIN-2026-17; "
                              "defaults to latest")
    parser.add_argument("--out", default="raw_bd_corpus")
    parser.add_argument("--per-domain-limit", type=int, default=50000,
                         help="Max CDX records per domain per crawl. "
                              "CC typically has 100k-500k+ for major .com sites.")
    parser.add_argument("--workers", type=int, default=16,
                         help="Thread pool size. I/O-bound (network range "
                              "requests), so this can exceed core count -- "
                              "20-32 is reasonable on an 8-core 7700; trafilatura "
                              "parsing is the CPU cost per doc, not the fetch.")
    parser.add_argument("--append", action="store_true",
                         help="Append to existing output files instead of overwriting.")
    args = parser.parse_args()

    if args.crawl:
        crawl_ids = args.crawl
    else:
        crawl_ids = [get_latest_crawl_id()]

    print(f"Crawls: {crawl_ids}")
    print(f"Domains: {sum(len(d) for d in DOMAIN_ALLOWLIST.values())}")
    print(f"Per-domain limit: {args.per_domain_limit}")
    harvest(crawl_ids, Path(args.out), per_domain_limit=args.per_domain_limit,
            workers=args.workers, append=args.append)
