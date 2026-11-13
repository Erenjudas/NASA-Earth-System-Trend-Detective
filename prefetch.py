"""Resumable prefetch tool for NASA POWER data collection.
Skips cached cities, applies rate limits, backoff retries, and circuit breaker.
"""

import time
import argparse
import sys
from pathlib import Path
from typing import Dict, List

from cities import get_cities
from data import fetch_live_nasa_power, CACHE_DIR, clean_dataframe

DELAY_BETWEEN_CITIES = 0.5
MAX_REPEATED_FAILURES = 3

def prefetch_all(force: bool = False, delay: float = DELAY_BETWEEN_CITIES) -> Dict[str, str]:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cities = get_cities(include_antarctica=False)
    results = {}
    consecutive_upstream_failures = 0

    print(f"Starting prefetch for {len(cities)} cities...")
    for idx, city_info in enumerate(cities, 1):
        city_name = city_info["city"]
        cache_file = CACHE_DIR / f"{city_name.lower()}_monthly.csv"

        # Resumable: skip cities already cached
        if not force and cache_file.exists() and cache_file.stat().st_size > 100:
            results[city_name] = "skipped_cached"
            print(f"[{idx}/{len(cities)}] {city_name}: already cached (skipped)")
            continue

        if consecutive_upstream_failures >= MAX_REPEATED_FAILURES:
            print(f"Stopping prefetch: {consecutive_upstream_failures} consecutive upstream 429/5xx failures.")
            results[city_name] = "stopped_circuit_breaker"
            break

        try:
            print(f"[{idx}/{len(cities)}] Fetching {city_name} from NASA POWER...")
            df = fetch_live_nasa_power(city_info, timeout=12.0, max_retries=3)
            # Save immediately after download
            df.to_csv(cache_file, index=False)
            results[city_name] = "downloaded"
            consecutive_upstream_failures = 0
            print(f"Saved {city_name} to {cache_file.name}")
        except Exception as exc:
            consecutive_upstream_failures += 1
            results[city_name] = f"failed: {exc}"
            print(f"Warning: Failed to download {city_name}: {exc}")

        # Small delay between cities
        time.sleep(delay)

    print("Prefetch finished.")
    return results

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Prefetch NASA POWER climate data")
    parser.add_argument("--force", action="store_true", help="Force redownload even if cached")
    parser.add_argument("--delay", type=float, default=DELAY_BETWEEN_CITIES, help="Delay between requests")
    args = parser.parse_args()

    prefetch_all(force=args.force, delay=args.delay)
