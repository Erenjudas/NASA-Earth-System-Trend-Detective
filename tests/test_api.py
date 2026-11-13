"""Pytest test cases for Earth System Trend Detective API.
Tests all 7 contract endpoints, error codes, edge cases, opposite trend logic, and fallback.
"""

import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient

from app import app
import data
from data import get_city_data
from cities import get_city

client = TestClient(app)

def test_endpoint_meta():
    res = client.get("/api/meta")
    assert res.status_code == 200
    data = res.json()
    for key in ["project", "parameters", "start_year", "end_year", "cities_count", "variables"]:
        assert key in data
    assert "precipitation" in data["variables"]
    assert "soil_moisture" in data["variables"]

def test_endpoint_status():
    res = client.get("/api/status")
    assert res.status_code == 200
    data = res.json()
    for key in ["status", "mode", "cached_count", "cached_cities", "demo"]:
        assert key in data
    assert data["status"] == "ok"

def test_endpoint_cities():
    res = client.get("/api/cities")
    assert res.status_code == 200
    cities = res.json()
    assert isinstance(cities, list)
    assert len(cities) >= 39
    first = cities[0]
    for key in ["city", "name", "continent", "latitude", "longitude", "country", "wettest_month"]:
        assert key in first

def test_endpoint_trend_success():
    res = client.get("/api/trend?city=Dhaka&variable=precipitation")
    assert res.status_code == 200
    data = res.json()
    for key in [
        "city", "variable", "valid_years", "pct_per_decade",
        "pct_per_decade_lower_95", "pct_per_decade_upper_95",
        "mk_p_value", "sen_slope", "sen_intercept", "significant", "trend", "demo"
    ]:
        assert key in data
    assert data["city"] == "Dhaka"
    assert data["variable"] == "precipitation"

def test_endpoint_compare():
    res = client.get("/api/compare?city_a=Dhaka&city_b=Santiago")
    assert res.status_code == 200
    data = res.json()
    for key in ["city_a", "city_b", "precipitation", "soil_moisture", "opposite_trends", "demo"]:
        assert key in data
    assert data["city_a"] == "Dhaka"
    assert data["city_b"] == "Santiago"

def test_endpoint_opposites():
    res = client.get("/api/opposites")
    assert res.status_code == 200
    data = res.json()
    assert "precipitation" in data
    assert "soil_moisture" in data
    if data["precipitation"]:
        item = data["precipitation"][0]
        for key in ["variable", "city_increasing", "city_decreasing", "increasing_pct_per_decade", "decreasing_pct_per_decade", "trend_gap_pct_points"]:
            assert key in item

def test_endpoint_clusters():
    res = client.get("/api/clusters")
    assert res.status_code == 200
    clusters = res.json()
    assert isinstance(clusters, list)
    assert len(clusters) >= 39
    item = clusters[0]
    for key in ["city", "precipitation_pct_per_decade", "soil_moisture_pct_per_decade", "cluster"]:
        assert key in item

def test_unknown_city_returns_404():
    res = client.get("/api/trend?city=AtlantisNonExistent&variable=precipitation")
    assert res.status_code == 404
    data = res.json()
    assert "error" in data
    assert "detail" in data
    assert "not found" in data["detail"].lower()

def test_bad_variable_returns_400():
    res = client.get("/api/trend?city=Dhaka&variable=nonexistent_var")
    assert res.status_code == 400
    data = res.json()
    assert "error" in data
    assert "detail" in data
    assert "invalid variable" in data["detail"].lower()

def test_antarctica_soil_moisture_na():
    res = client.get("/api/trend?city=Antarctica&variable=soil_moisture")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "n/a"
    assert "reason" in data
    assert "no soil-moisture data over ice" in data["reason"].lower()
    assert data["significant"] is False
    assert data["trend"] == "n/a"

def test_opposite_trend_logic():
    res = client.get("/api/opposites")
    assert res.status_code == 200
    data = res.json()
    for var in ["precipitation", "soil_moisture"]:
        pairs = data[var]
        for pair in pairs:
            # Both must have significant p-values (< 0.05) and opposite signs
            assert pair["increasing_pct_per_decade"] > 0
            assert pair["decreasing_pct_per_decade"] < 0
            assert pair["increasing_p_value"] < 0.05
            assert pair["decreasing_p_value"] < 0.05
            assert pair["city_increasing"] != pair["city_decreasing"]
            assert pair["trend_gap_pct_points"] > 0

def test_mocked_nasa_failure_fallback():
    # Test that when live NASA call fails and no cache exists, synthetic fallback activates with demo=True
    with patch("data.PROCESSED_DIR", new=data.BASE_DIR / "nonexistent_dir"), \
         patch("data.CACHE_DIR", new=data.BASE_DIR / "nonexistent_dir"), \
         patch("data.requests.get", side_effect=Exception("Connection refused / 502 Upstream Error")):
        df, is_demo = get_city_data("Dhaka")
        assert is_demo is True
        assert not df.empty
        assert len(df) == 540  # 45 years * 12 months
        assert "precipitation" in df.columns
        assert "soil_moisture" in df.columns
