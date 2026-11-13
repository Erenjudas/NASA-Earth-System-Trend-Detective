# Earth System Trend Detective API Documentation

Base path: `/api/`

All successful responses return JSON HTTP 200.
Errors return JSON with `{ "error": "<Summary>", "detail": "<Detailed explanation>" }`.

---

## 1. Metadata (`GET /api/meta`)
Returns project metadata, variables, coverage period, and city counts.

**Response (200 OK):**
```json
{
  "project": "NASA Earth System Trend Detective",
  "parameters": ["PRECTOTCORR", "GWETROOT"],
  "start_year": 1981,
  "end_year": 2025,
  "cities_count": 39,
  "variables": {
    "precipitation": {"unit": "mm/day", "code": "PRECTOTCORR"},
    "soil_moisture": {"unit": "0-1", "code": "GWETROOT"}
  }
}
```

---

## 2. Status (`GET /api/status`)
Returns server status, current data mode (`live` or `demo`), and cache inventory.

**Response (200 OK):**
```json
{
  "status": "ok",
  "mode": "live",
  "cached_count": 39,
  "cached_cities": ["Islamabad", "Delhi", "..."],
  "demo": false
}
```

---

## 3. Cities (`GET /api/cities`)
Returns the list of 39 global benchmark cities and Antarctica.

**Response (200 OK):**
```json
[
  {
    "city": "Islamabad",
    "name": "Islamabad",
    "continent": "Asia",
    "latitude": 33.6844,
    "longitude": 73.0479,
    "country": "Pakistan",
    "wettest_month": "July",
    "n": "Islamabad",
    "c": "Asia",
    "lat": 33.6844,
    "lon": 73.0479,
    "k": "Pakistan",
    "w": "July"
  }
]
```

---

## 4. Trend (`GET /api/trend`)
Returns Mann-Kendall and Sen's slope trend analysis for a specific city and variable.

**Query Parameters:**
- `city` (string, required): City name (e.g. `Dhaka`, `Santiago`, `Antarctica`).
- `variable` (string, required): `precipitation` or `soil_moisture` (also accepts `p` or `s`).

**Response (200 OK):**
```json
{
  "city": "Islamabad",
  "variable": "precipitation",
  "valid_years": 45,
  "pct_per_decade": 11.1428,
  "pct_per_decade_lower_95": 0.3989,
  "pct_per_decade_upper_95": 23.0613,
  "mk_p_value": 0.033774,
  "sen_slope": 0.030262,
  "sen_intercept": -58.058781,
  "significant": true,
  "robust": false,
  "trend": "rising",
  "demo": false
}
```

**Antarctica Edge Case (200 OK):**
```json
{
  "city": "Antarctica",
  "variable": "soil_moisture",
  "status": "n/a",
  "reason": "no soil-moisture data over ice",
  "trend": "n/a",
  "valid_years": 0,
  "significant": false,
  "demo": false
}
```

**Errors:**
- `404 Not Found`: Unknown city: `{ "error": "City not found", "detail": "City 'Atlantis' not found" }`
- `400 Bad Request`: Invalid variable: `{ "error": "Invalid variable", "detail": "Variable must be precipitation or soil_moisture" }`

---

## 5. Compare (`GET /api/compare`)
Compares trends and metrics between two cities.

**Query Parameters:**
- `city_a` (string, required): First city name.
- `city_b` (string, required): Second city name.

**Response (200 OK):**
```json
{
  "city_a": "Dhaka",
  "city_b": "Santiago",
  "precipitation": {
    "city_a": { "pct_per_decade": 20.64, "significant": true },
    "city_b": { "pct_per_decade": -16.58, "significant": true }
  },
  "soil_moisture": {
    "city_a": { "pct_per_decade": 0.82, "significant": false },
    "city_b": { "pct_per_decade": -2.14, "significant": true }
  },
  "opposite_trends": ["precipitation"],
  "demo": false
}
```

---

## 6. Opposites (`GET /api/opposites`)
Returns ranked city pairs with statistically significant opposite trends (one rising, one falling, both $p < 0.05$).

**Response (200 OK):**
```json
{
  "precipitation": [
    {
      "variable": "precipitation",
      "city_increasing": "Dhaka",
      "city_decreasing": "Santiago",
      "increasing_pct_per_decade": 20.643,
      "decreasing_pct_per_decade": -16.576,
      "trend_gap_pct_points": 37.22,
      "increasing_p_value": 0.000000018,
      "decreasing_p_value": 0.000235,
      "demo": false
    }
  ],
  "soil_moisture": [ ... ]
}
```

---

## 7. Clusters (`GET /api/clusters`)
Returns K-Means trend-based groupings across benchmark cities.

**Response (200 OK):**
```json
[
  {
    "city": "Accra",
    "precipitation_pct_per_decade": 5.433,
    "soil_moisture_pct_per_decade": 2.567,
    "cluster": 1
  }
]
```

---

## Additional Frontend Endpoints (contract for `static/api.js`)
- `GET /api/series` (or `/series`): Monthly/annual series data.
- `GET /api/forecasts` (or `/forecasts`): 10-year linear forecasts (2026–2035).
