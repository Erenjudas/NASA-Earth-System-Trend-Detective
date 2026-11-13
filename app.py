"""Earth System Trend Detective Backend API.
Serves NASA climate trends, comparisons, clusters, and opposites.
"""

import os
from pathlib import Path
from contextlib import asynccontextmanager
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, Query, HTTPException, Request
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from cities import get_cities, get_city, normalize_key, CITIES, ANTARCTICA_CITY
from data import CACHE_DIR, PROCESSED_DIR, BASE_DIR, get_city_data
from stats import (
    compute_trend_for_variable,
    get_all_trends,
    get_opposite_trends,
    get_clusters,
    compute_annual_series,
    _SERIES_CACHE,
    _TREND_CACHE
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Precompute in memory at startup so request handlers never recompute
    try:
        get_all_trends()
        get_opposite_trends()
        get_clusters()
    except Exception as exc:
        print(f"Startup cache warming warning: {exc}")
    yield

app = FastAPI(
    title="Earth System Trend Detective API",
    description="NASA Space Apps 2026 - Environmental Trend Detection",
    version="1.0.0",
    lifespan=lifespan
)

# 7. CORS enabled for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Uniform JSON Error Handling { "error": ..., "detail": ... }
@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request: Request, exc: HTTPException):
    detail = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
    error_summary = {
        400: "Bad Request",
        404: "Not Found",
        500: "Internal Server Error",
        502: "Bad Gateway"
    }.get(exc.status_code, "Error")

    return JSONResponse(
        status_code=exc.status_code,
        content={"error": error_summary, "detail": detail}
    )

@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"error": "Internal Server Error", "detail": str(exc)}
    )



# -------------------------------------------------------------
# 1. /api/meta
# -------------------------------------------------------------
@app.get("/api/meta")
@app.get("/meta")
def get_meta():
    return {
        "project": "NASA Earth System Trend Detective",
        "parameters": ["PRECTOTCORR", "GWETROOT"],
        "start_year": 1981,
        "end_year": 2025,
        "cities_count": len(CITIES),
        "variables": {
            "precipitation": {"unit": "mm/day", "code": "PRECTOTCORR"},
            "soil_moisture": {"unit": "0-1", "code": "GWETROOT"}
        }
    }

# -------------------------------------------------------------
# 2. /api/status
# -------------------------------------------------------------
@app.get("/api/status")
@app.get("/status")
def get_status():
    cached_files = list(CACHE_DIR.glob("*_monthly.csv")) if CACHE_DIR.exists() else []
    cached_names = [f.stem.replace("_monthly", "").title() for f in cached_files]
    mode = "live" if len(cached_files) > 0 else "demo"
    return {
        "status": "ok",
        "mode": mode,
        "cached_count": len(cached_files),
        "cached_cities": cached_names,
        "demo": (mode == "demo")
    }

# -------------------------------------------------------------
# 3. /api/cities
# -------------------------------------------------------------
@app.get("/api/cities")
@app.get("/cities")
def list_cities():
    return get_cities(include_antarctica=False)

# -------------------------------------------------------------
# 4. /api/trend and /api/trends
# -------------------------------------------------------------
@app.get("/api/trend")
@app.get("/trend")
@app.get("/api/trends")
@app.get("/trends")
def get_trend(
    city: Optional[str] = Query(None, description="City name"),
    variable: Optional[str] = Query(None, description="Variable (precipitation or soil_moisture)")
):
    # If no city provided, return all precomputed trends
    if not city:
        return get_all_trends()

    city_info = get_city(city)
    if not city_info:
        raise HTTPException(status_code=404, detail=f"City '{city}' not found")

    if variable:
        var_norm = str(variable).strip().lower()
        if var_norm in ("p", "precipitation", "prectotcorr"):
            var_key = "precipitation"
        elif var_norm in ("s", "soil_moisture", "soil", "gwetroot"):
            var_key = "soil_moisture"
        else:
            raise HTTPException(status_code=400, detail=f"Invalid variable '{variable}'. Must be precipitation or soil_moisture.")
        return compute_trend_for_variable(city_info["city"], var_key)

    # Return both variables for the city
    p_trend = compute_trend_for_variable(city_info["city"], "precipitation")
    s_trend = compute_trend_for_variable(city_info["city"], "soil_moisture")
    return [p_trend, s_trend]

# -------------------------------------------------------------
# 5. /api/compare
# -------------------------------------------------------------
@app.get("/api/compare")
@app.get("/compare")
def compare_cities(
    city_a: Optional[str] = Query(None, description="First city"),
    city_b: Optional[str] = Query(None, description="Second city"),
    city1: Optional[str] = Query(None, description="Alias for city_a"),
    city2: Optional[str] = Query(None, description="Alias for city_b")
):
    c_a = city_a or city1
    c_b = city_b or city2

    if not c_a or not c_b:
        raise HTTPException(status_code=400, detail="Parameters city_a and city_b are required")

    info_a = get_city(c_a)
    if not info_a:
        raise HTTPException(status_code=404, detail=f"City '{c_a}' not found")

    info_b = get_city(c_b)
    if not info_b:
        raise HTTPException(status_code=404, detail=f"City '{c_b}' not found")

    t_a_p = compute_trend_for_variable(info_a["city"], "precipitation")
    t_b_p = compute_trend_for_variable(info_b["city"], "precipitation")
    t_a_s = compute_trend_for_variable(info_a["city"], "soil_moisture")
    t_b_s = compute_trend_for_variable(info_b["city"], "soil_moisture")

    opposite_vars = []
    if (t_a_p["significant"] and t_b_p["significant"] and
            (t_a_p["pct_per_decade"] * t_b_p["pct_per_decade"] < 0)):
        opposite_vars.append("precipitation")

    if (t_a_s["significant"] and t_b_s["significant"] and
            (t_a_s["pct_per_decade"] * t_b_s["pct_per_decade"] < 0)):
        opposite_vars.append("soil_moisture")

    is_demo = (t_a_p.get("demo", False) or t_b_p.get("demo", False) or
               t_a_s.get("demo", False) or t_b_s.get("demo", False))

    return {
        "city_a": info_a["city"],
        "city_b": info_b["city"],
        "precipitation": {
            "city_a": {"pct_per_decade": t_a_p["pct_per_decade"], "significant": t_a_p["significant"], "p_value": t_a_p["mk_p_value"]},
            "city_b": {"pct_per_decade": t_b_p["pct_per_decade"], "significant": t_b_p["significant"], "p_value": t_b_p["mk_p_value"]}
        },
        "soil_moisture": {
            "city_a": {"pct_per_decade": t_a_s["pct_per_decade"], "significant": t_a_s["significant"], "p_value": t_a_s["mk_p_value"]},
            "city_b": {"pct_per_decade": t_b_s["pct_per_decade"], "significant": t_b_s["significant"], "p_value": t_b_s["mk_p_value"]}
        },
        "opposite_trends": opposite_vars,
        "demo": is_demo
    }

# -------------------------------------------------------------
# 6. /api/opposites and /api/opposite-trends
# -------------------------------------------------------------
@app.get("/api/opposites")
@app.get("/opposites")
@app.get("/api/opposite-trends")
@app.get("/opposite-trends")
def get_opposites():
    return get_opposite_trends()

# -------------------------------------------------------------
# 7. /api/clusters
# -------------------------------------------------------------
@app.get("/api/clusters")
@app.get("/clusters")
def list_clusters():
    return get_clusters()

# -------------------------------------------------------------
# Frontend Helper Endpoints for static/api.js
# -------------------------------------------------------------
@app.get("/api/series")
@app.get("/series")
def get_all_series():
    """Return historical time series records for all 39 cities."""
    rows = []
    for city_info in get_cities(include_antarctica=False):
        c_name = city_info["city"]
        df, _ = get_city_data(c_name)
        ann_p = compute_annual_series(df, "precipitation").set_index("year")["value"].to_dict()
        ann_s = compute_annual_series(df, "soil_moisture").set_index("year")["value"].to_dict()
        for yr in range(1981, 2026):
            rows.append({
                "city": c_name,
                "name": c_name,
                "year": yr,
                "date": f"{yr}-01-01",
                "precipitation": ann_p.get(yr, None),
                "soil_moisture": ann_s.get(yr, None)
            })
    return rows

@app.get("/api/forecasts")
@app.get("/forecasts")
def get_all_forecasts():
    """Return 10-year projections (2026-2035) for static/api.js."""
    forecast_file = BASE_DIR / "outputs" / "all_cities_10_year_forecasts.csv"
    if forecast_file.exists():
        import pandas as pd
        df = pd.read_csv(forecast_file)
        return df.to_dict(orient="records")

    # Generate linear projection based on trends
    rows = []
    for city_info in get_cities(include_antarctica=False):
        c_name = city_info["city"]
        tp = compute_trend_for_variable(c_name, "precipitation")
        ts = compute_trend_for_variable(c_name, "soil_moisture")
        for yr in range(2026, 2036):
            p_val = max(0.0, tp["sen_intercept"] + tp["sen_slope"] * yr)
            s_val = min(1.0, max(0.0, ts["sen_intercept"] + ts["sen_slope"] * yr))
            rows.append({
                "city": c_name,
                "year": yr,
                "precipitation": round(p_val, 4),
                "soil_moisture": round(s_val, 4),
                "lower_bound": round(p_val * 0.9, 4),
                "upper_bound": round(p_val * 1.1, 4)
            })
    return rows

# -------------------------------------------------------------
# Static Frontend Serving
# -------------------------------------------------------------
static_dir = BASE_DIR / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    @app.get("/")
    def serve_index():
        return FileResponse(str(static_dir / "index.html"))

    @app.get("/api.js")
    def serve_api_js():
        return FileResponse(str(static_dir / "api.js"))

if __name__ == "__main__":
    import uvicorn
    # Read PORT from env
    port = int(os.environ.get("PORT", 8000))
    print(f"Starting Earth System Trend Detective API on port {port}...")
    uvicorn.run(app, host="0.0.0.0", port=port)
