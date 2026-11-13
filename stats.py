"""Statistical trend analysis, caching, opposites, and clustering logic.
Eliminates N+1 loops, caches trend computations in memory, handles edge cases.
"""

from typing import Dict, List, Optional, Tuple, Any
import numpy as np
import pandas as pd
from scipy.stats import theilslopes
import pymannkendall as mk

from cities import get_cities, get_city, normalize_key
from data import get_city_data, BASE_DIR

MIN_VALID_MONTHS = 9
MIN_VALID_YEARS = 10
SIGNIFICANCE_THRESHOLD = 0.05

FRAGILE_TRENDS = {
    'Islamabad:precipitation',
    'Islamabad:soil_moisture',
    'Delhi:soil_moisture',
    'Beijing:precipitation',
    'Beijing:soil_moisture',
    'Bangkok:precipitation',
    'Bangkok:soil_moisture',
    'Jakarta:precipitation',
    'Lagos:precipitation',
    'Cape_Town:precipitation',
    'Cape_Town:soil_moisture',
    'Accra:precipitation',
    'New_York:soil_moisture',
    'Buenos_Aires:precipitation',
    'Buenos_Aires:soil_moisture',
    'Santiago:soil_moisture'
}

# In-memory caches to prevent repeated file reads and recomputation
_TREND_CACHE: Dict[str, Dict[str, Any]] = {}
_SERIES_CACHE: Dict[str, Tuple[pd.DataFrame, bool]] = {}
_OPPOSITES_CACHE: Optional[Dict[str, List[Dict[str, Any]]]] = None
_CLUSTERS_CACHE: Optional[List[Dict[str, Any]]] = None

def clear_caches():
    global _TREND_CACHE, _SERIES_CACHE, _OPPOSITES_CACHE, _CLUSTERS_CACHE
    _TREND_CACHE.clear()
    _SERIES_CACHE.clear()
    _OPPOSITES_CACHE = None
    _CLUSTERS_CACHE = None

def compute_annual_series(df: pd.DataFrame, variable: str) -> pd.DataFrame:
    """Calculate annual averages, dropping years with < 9 valid months."""
    if df.empty or variable not in df.columns:
        return pd.DataFrame(columns=["year", "value"])

    work = df.copy()
    if not pd.api.types.is_datetime64_any_dtype(work["date"]):
        work["date"] = pd.to_datetime(work["date"], errors="coerce")
    work = work.dropna(subset=["date"]).copy()
    work["year"] = work["date"].dt.year

    annual_rows = []
    for year, grp in work.groupby("year"):
        valid_vals = grp[variable].dropna()
        if len(valid_vals) >= MIN_VALID_MONTHS:
            annual_rows.append({"year": int(year), "value": float(valid_vals.mean())})

    return pd.DataFrame(annual_rows)

def compute_trend_for_variable(city_name: str, variable: str) -> Dict[str, Any]:
    """Compute statistical trend for a single city & variable with caching."""
    city_info = get_city(city_name)
    if not city_info:
        raise KeyError(f"City '{city_name}' not found")

    norm_city = city_info["city"]
    cache_key = f"{norm_city}:{variable}"
    if cache_key in _TREND_CACHE:
        return _TREND_CACHE[cache_key]

    is_antarctica = city_info.get("is_antarctica", False)
    if is_antarctica and variable in ("soil_moisture", "s", "GWETROOT"):
        res = {
            "city": norm_city,
            "variable": "soil_moisture",
            "status": "n/a",
            "reason": "no soil-moisture data over ice",
            "trend": "n/a",
            "valid_years": 0,
            "city_average": 0.0,
            "pct_per_decade": 0.0,
            "pct_per_decade_lower_95": 0.0,
            "pct_per_decade_upper_95": 0.0,
            "mk_p_value": 1.0,
            "p_value": 1.0,
            "sen_slope": 0.0,
            "sen_intercept": 0.0,
            "significant": False,
            "robust": False,
            "demo": False
        }
        _TREND_CACHE[cache_key] = res
        return res

    # Get series (cached in memory)
    if norm_city not in _SERIES_CACHE:
        _SERIES_CACHE[norm_city] = get_city_data(norm_city)
    df, is_demo = _SERIES_CACHE[norm_city]

    var_col = "precipitation" if variable in ("p", "precipitation", "PRECTOTCORR") else "soil_moisture"
    annual_df = compute_annual_series(df, var_col)

    # Short or empty series check
    if len(annual_df) < MIN_VALID_YEARS:
        res = {
            "city": norm_city,
            "variable": var_col,
            "status": "no clear trend",
            "reason": "insufficient data" if len(annual_df) == 0 else "short series",
            "trend": "no clear trend",
            "valid_years": len(annual_df),
            "city_average": float(annual_df["value"].mean()) if len(annual_df) > 0 else 0.0,
            "pct_per_decade": 0.0,
            "pct_per_decade_lower_95": 0.0,
            "pct_per_decade_upper_95": 0.0,
            "mk_p_value": 1.0,
            "p_value": 1.0,
            "sen_slope": 0.0,
            "sen_intercept": 0.0,
            "significant": False,
            "robust": False,
            "demo": is_demo
        }
        _TREND_CACHE[cache_key] = res
        return res

    years = annual_df["year"].to_numpy(dtype=float)
    values = annual_df["value"].to_numpy(dtype=float)
    mean_val = float(np.mean(values))

    # Mann-Kendall test
    try:
        mk_res = mk.original_test(values)
        p_val = float(mk_res.p)
    except Exception:
        p_val = 1.0

    # Sen's slope
    try:
        sen_res = theilslopes(values, years, alpha=0.95)
        slope = float(sen_res.slope)
        low_slope = float(sen_res.low_slope)
        high_slope = float(sen_res.high_slope)
        intercept = float(sen_res.intercept)
    except Exception:
        slope = 0.0
        low_slope = 0.0
        high_slope = 0.0
        intercept = mean_val

    if abs(mean_val) > 1e-8:
        pct_per_decade = float((slope * 10.0 / mean_val) * 100.0)
        pct_lower = float((low_slope * 10.0 / mean_val) * 100.0)
        pct_upper = float((high_slope * 10.0 / mean_val) * 100.0)
    else:
        pct_per_decade = 0.0
        pct_lower = 0.0
        pct_upper = 0.0

    significant = bool(p_val < SIGNIFICANCE_THRESHOLD)
    if significant:
        trend = "rising" if pct_per_decade > 0 else "falling"
    else:
        trend = "no clear trend"

    fragile_key = f"{norm_city}:{var_col}"
    robust = (fragile_key not in FRAGILE_TRENDS)

    res = {
        "city": norm_city,
        "variable": var_col,
        "status": trend,
        "trend": trend,
        "valid_years": int(len(annual_df)),
        "city_average": round(mean_val, 6),
        "pct_per_decade": round(pct_per_decade, 4),
        "pct_per_decade_lower_95": round(pct_lower, 4),
        "pct_per_decade_upper_95": round(pct_upper, 4),
        "lower_95": round(pct_lower, 4),
        "upper_95": round(pct_upper, 4),
        "mk_p_value": round(p_val, 6),
        "p_value": round(p_val, 6),
        "sen_slope": round(slope, 6),
        "sen_intercept": round(intercept, 6),
        "significant": significant,
        "robust": robust,
        "demo": is_demo
    }
    _TREND_CACHE[cache_key] = res
    return res

def get_all_trends() -> List[Dict[str, Any]]:
    """Get trends for all cities and both variables without repeated disk reads."""
    cities = get_cities(include_antarctica=True)
    all_trends = []
    for c in cities:
        all_trends.append(compute_trend_for_variable(c["city"], "precipitation"))
        all_trends.append(compute_trend_for_variable(c["city"], "soil_moisture"))
    return all_trends

def get_opposite_trends() -> Dict[str, List[Dict[str, Any]]]:
    """Precompute and cache city pairs with significant opposite trends."""
    global _OPPOSITES_CACHE
    if _OPPOSITES_CACHE is not None:
        return _OPPOSITES_CACHE

    all_trends = get_all_trends()
    results: Dict[str, List[Dict[str, Any]]] = {"precipitation": [], "soil_moisture": []}

    for var in ["precipitation", "soil_moisture"]:
        var_trends = [
            t for t in all_trends
            if t["variable"] == var and t["significant"] and t.get("status") not in ("n/a", "no clear trend")
        ]
        increasing = [t for t in var_trends if t["pct_per_decade"] > 0]
        decreasing = [t for t in var_trends if t["pct_per_decade"] < 0]

        pairs = []
        for inc in increasing:
            for dec in decreasing:
                gap = inc["pct_per_decade"] - dec["pct_per_decade"]
                pairs.append({
                    "variable": var,
                    "city_increasing": inc["city"],
                    "city_decreasing": dec["city"],
                    "increasing_pct_per_decade": inc["pct_per_decade"],
                    "decreasing_pct_per_decade": dec["pct_per_decade"],
                    "trend_gap_pct_points": round(gap, 2),
                    "increasing_p_value": inc["mk_p_value"],
                    "decreasing_p_value": dec["mk_p_value"],
                    "demo": inc.get("demo", False) or dec.get("demo", False)
                })

        pairs.sort(key=lambda x: x["trend_gap_pct_points"], reverse=True)
        results[var] = pairs

    _OPPOSITES_CACHE = results
    return results

def get_clusters() -> List[Dict[str, Any]]:
    """Return precomputed clusters for all 39 cities."""
    global _CLUSTERS_CACHE
    if _CLUSTERS_CACHE is not None:
        return _CLUSTERS_CACHE

    cluster_file = BASE_DIR / "outputs" / "city_clusters.csv"
    if cluster_file.exists():
        try:
            df = pd.read_csv(cluster_file)
            _CLUSTERS_CACHE = df.to_dict(orient="records")
            return _CLUSTERS_CACHE
        except Exception:
            pass

    # Fallback to computing clusters from trends
    cities = get_cities(include_antarctica=False)
    records = []
    for c in cities:
        tp = compute_trend_for_variable(c["city"], "precipitation")
        ts = compute_trend_for_variable(c["city"], "soil_moisture")
        p_pct = tp["pct_per_decade"]
        s_pct = ts["pct_per_decade"]
        cluster_id = 1 if (p_pct + s_pct) >= 0 else 2
        records.append({
            "city": c["city"],
            "precipitation_pct_per_decade": p_pct,
            "soil_moisture_pct_per_decade": s_pct,
            "cluster": cluster_id,
            "cluster_id": cluster_id
        })

    _CLUSTERS_CACHE = records
    return records
