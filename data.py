"""Data loading and live NASA POWER ingestion with 4-tier fallback:
CSV -> Cache -> Live NASA POWER -> Synthetic Demo.
"""

import time
import requests
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, Optional, Tuple

from cities import get_city, normalize_key, ANTARCTICA_CITY

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
PROCESSED_DIR = DATA_DIR / "processed"
CACHE_DIR = DATA_DIR / "cache"
RAW_DIR = DATA_DIR / "raw"

NASA_API_URL = "https://power.larc.nasa.gov/api/temporal/monthly/point"
START_YEAR = 1981
END_YEAR = 2025

# Quota safety tracking
_consecutive_upstream_errors = 0
MAX_CONSECUTIVE_ERRORS = 3

def reset_upstream_error_counter():
    global _consecutive_upstream_errors
    _consecutive_upstream_errors = 0

def clean_dataframe(df: pd.DataFrame, city_name: str, is_antarctica: bool = False) -> pd.DataFrame:
    """Standardize, clean, and validate monthly dataframe."""
    df = df.copy()
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df = df.dropna(subset=["date"]).copy()
    elif "year" in df.columns and "month" in df.columns:
        df["date"] = pd.to_datetime(df["year"].astype(str) + "-" + df["month"].astype(str) + "-01", errors="coerce")
        df = df.dropna(subset=["date"]).copy()

    for col in ["precipitation", "soil_moisture"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
            # Handle NASA -999 missing sentinel values
            df.loc[df[col] <= -900, col] = np.nan

    if "precipitation" in df.columns:
        df.loc[df["precipitation"] < 0, "precipitation"] = np.nan

    if "soil_moisture" in df.columns:
        if is_antarctica:
            df["soil_moisture"] = np.nan
        else:
            df.loc[(df["soil_moisture"] < 0) | (df["soil_moisture"] > 1), "soil_moisture"] = np.nan

    df["city"] = city_name
    return df.sort_values("date").reset_index(drop=True)

def generate_synthetic_series(city_info: Dict) -> pd.DataFrame:
    """Generate realistic synthetic demo data when upstream is unavailable."""
    dates = pd.date_range(start=f"{START_YEAR}-01-01", end=f"{END_YEAR}-12-01", freq="MS")
    n = len(dates)
    rng = np.random.RandomState(abs(hash(city_info["city"])) % (2**31 - 1))

    is_antarctica = city_info.get("is_antarctica", False)
    months = dates.month.values

    # Base seasonal cycle
    seasonal_precip = 2.0 + 1.5 * np.sin(2 * np.pi * (months - 3) / 12)
    noise_p = rng.normal(0, 0.4, n)
    precip = np.clip(seasonal_precip + noise_p, 0.05, None)

    if is_antarctica:
        soil = np.full(n, np.nan)
        precip = np.clip(0.2 + rng.normal(0, 0.05, n), 0.01, None)
    else:
        seasonal_soil = 0.45 + 0.15 * np.cos(2 * np.pi * (months - 4) / 12)
        noise_s = rng.normal(0, 0.05, n)
        soil = np.clip(seasonal_soil + noise_s, 0.01, 0.99)

    return pd.DataFrame({
        "date": dates,
        "precipitation": np.round(precip, 3),
        "soil_moisture": np.round(soil, 3),
        "city": city_info["city"]
    })

def fetch_live_nasa_power(city_info: Dict, timeout: float = 12.0, max_retries: int = 3) -> pd.DataFrame:
    """Fetch monthly records from NASA POWER API with retries and exponential backoff."""
    global _consecutive_upstream_errors
    if _consecutive_upstream_errors >= MAX_CONSECUTIVE_ERRORS:
        raise ConnectionError(f"Upstream safety circuit tripped: {_consecutive_upstream_errors} repeated 429/5xx errors.")

    params = {
        "parameters": "PRECTOTCORR,GWETROOT",
        "community": "RE",
        "longitude": city_info["longitude"],
        "latitude": city_info["latitude"],
        "start": START_YEAR,
        "end": END_YEAR,
        "format": "JSON"
    }

    last_error = None
    for attempt in range(1, max_retries + 1):
        try:
            resp = requests.get(NASA_API_URL, params=params, timeout=timeout)
            if resp.status_code in (429, 500, 502, 503, 504):
                _consecutive_upstream_errors += 1
                resp.raise_for_status()

            resp.raise_for_status()
            data = resp.json()

            properties = data.get("properties", {})
            param_data = properties.get("parameter", {})
            rainfall = param_data.get("PRECTOTCORR", {})
            soil = param_data.get("GWETROOT", {})

            records = []
            is_antarctica = city_info.get("is_antarctica", False)
            for date_key in sorted(rainfall.keys()):
                d_str = str(date_key)
                if len(d_str) != 6 or not d_str.isdigit():
                    continue
                year = int(d_str[:4])
                month = int(d_str[4:6])
                if not (START_YEAR <= year <= END_YEAR) or not (1 <= month <= 12):
                    continue

                date = f"{year:04d}-{month:02d}-01"
                p_val = rainfall.get(date_key, np.nan)
                s_val = soil.get(date_key, np.nan)

                records.append({
                    "date": date,
                    "precipitation": p_val,
                    "soil_moisture": np.nan if is_antarctica else s_val,
                    "city": city_info["city"]
                })

            df = pd.DataFrame(records)
            _consecutive_upstream_errors = 0
            return clean_dataframe(df, city_info["city"], is_antarctica=is_antarctica)

        except Exception as exc:
            last_error = exc
            if attempt < max_retries:
                sleep_time = 0.5 * (2 ** (attempt - 1))
                time.sleep(sleep_time)

    _consecutive_upstream_errors += 1
    raise ConnectionError(f"Failed to fetch NASA POWER data after {max_retries} attempts: {last_error}")

def get_city_data(city_name: str) -> Tuple[pd.DataFrame, bool]:
    """Retrieve city time series using the 4-tier fallback:
    CSV -> Cache -> Live NASA POWER -> Synthetic Demo.
    Returns (df, is_demo).
    """
    city_info = get_city(city_name)
    if not city_info:
        raise KeyError(f"Unknown city: {city_name}")

    canonical_name = city_info["city"]
    lower_name = canonical_name.lower()
    is_antarctica = city_info.get("is_antarctica", False)

    # 1. Tier 1: Processed CSV
    processed_path = PROCESSED_DIR / f"{lower_name}_cleaned.csv"
    if processed_path.exists():
        try:
            df = pd.read_csv(processed_path)
            if not df.empty:
                return clean_dataframe(df, canonical_name, is_antarctica=is_antarctica), False
        except Exception:
            pass

    # 2. Tier 2: Cache CSV
    cache_path = CACHE_DIR / f"{lower_name}_monthly.csv"
    if cache_path.exists():
        try:
            df = pd.read_csv(cache_path)
            if not df.empty:
                return clean_dataframe(df, canonical_name, is_antarctica=is_antarctica), False
        except Exception:
            pass

    # 3. Tier 3: Live NASA POWER call (never called if cache exists)
    try:
        df = fetch_live_nasa_power(city_info)
        # Save each city right after download
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        df.to_csv(cache_path, index=False)
        return df, False
    except Exception:
        # Fallback to Tier 4
        pass

    # 4. Tier 4: Synthetic Demo Data (always flagged demo=True)
    df_synthetic = generate_synthetic_series(city_info)
    return df_synthetic, True
