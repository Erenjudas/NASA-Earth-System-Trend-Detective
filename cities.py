"""City metadata and utilities for Earth System Trend Detective."""

from typing import Dict, List, Optional

RAW_CITIES: List[Dict] = [
    {"n": "Islamabad", "c": "Asia", "lat": 33.6844, "lon": 73.0479, "k": "Pakistan", "w": "July"},
    {"n": "Delhi", "c": "Asia", "lat": 28.6139, "lon": 77.209, "k": "India", "w": "August"},
    {"n": "Beijing", "c": "Asia", "lat": 39.9042, "lon": 116.4074, "k": "China", "w": "July"},
    {"n": "Tokyo", "c": "Asia", "lat": 35.6762, "lon": 139.6503, "k": "Japan", "w": "September"},
    {"n": "Bangkok", "c": "Asia", "lat": 13.7563, "lon": 100.5018, "k": "Thailand", "w": "September"},
    {"n": "Riyadh", "c": "Asia", "lat": 24.7136, "lon": 46.6753, "k": "Saudi Arabia", "w": "March"},
    {"n": "Dhaka", "c": "Asia", "lat": 23.8103, "lon": 90.4125, "k": "Bangladesh", "w": "July"},
    {"n": "Jakarta", "c": "Asia", "lat": -6.2088, "lon": 106.8456, "k": "Indonesia", "w": "February"},
    {"n": "Cairo", "c": "Africa", "lat": 30.0444, "lon": 31.2357, "k": "Egypt", "w": "March"},
    {"n": "Lagos", "c": "Africa", "lat": 6.5244, "lon": 3.3792, "k": "Nigeria", "w": "June"},
    {"n": "Nairobi", "c": "Africa", "lat": -1.2921, "lon": 36.8219, "k": "Kenya", "w": "April"},
    {"n": "Cape_Town", "c": "Africa", "lat": -33.9249, "lon": 18.4241, "k": "South Africa", "w": "June"},
    {"n": "Addis_Ababa", "c": "Africa", "lat": 8.9806, "lon": 38.7578, "k": "Ethiopia", "w": "August"},
    {"n": "Accra", "c": "Africa", "lat": 5.6037, "lon": -0.187, "k": "Ghana", "w": "June"},
    {"n": "Casablanca", "c": "Africa", "lat": 33.5731, "lon": -7.5898, "k": "Morocco", "w": "November"},
    {"n": "London", "c": "Europe", "lat": 51.5072, "lon": -0.1276, "k": "United Kingdom", "w": "October"},
    {"n": "Paris", "c": "Europe", "lat": 48.8566, "lon": 2.3522, "k": "France", "w": "December"},
    {"n": "Berlin", "c": "Europe", "lat": 52.52, "lon": 13.405, "k": "Germany", "w": "July"},
    {"n": "Rome", "c": "Europe", "lat": 41.9028, "lon": 12.4964, "k": "Italy", "w": "November"},
    {"n": "Madrid", "c": "Europe", "lat": 40.4168, "lon": -3.7038, "k": "Spain", "w": "October"},
    {"n": "Moscow", "c": "Europe", "lat": 55.7558, "lon": 37.6173, "k": "Russia", "w": "July"},
    {"n": "Stockholm", "c": "Europe", "lat": 59.3293, "lon": 18.0686, "k": "Sweden", "w": "July"},
    {"n": "New_York", "c": "North America", "lat": 40.7128, "lon": -74.006, "k": "USA", "w": "July"},
    {"n": "Los_Angeles", "c": "North America", "lat": 34.0522, "lon": -118.2437, "k": "USA", "w": "February"},
    {"n": "Mexico_City", "c": "North America", "lat": 19.4326, "lon": -99.1332, "k": "Mexico", "w": "July"},
    {"n": "Toronto", "c": "North America", "lat": 43.6532, "lon": -79.3832, "k": "Canada", "w": "June"},
    {"n": "Miami", "c": "North America", "lat": 25.7617, "lon": -80.1918, "k": "USA", "w": "June"},
    {"n": "Chicago", "c": "North America", "lat": 41.8781, "lon": -87.6298, "k": "USA", "w": "May"},
    {"n": "Vancouver", "c": "North America", "lat": 49.2827, "lon": -123.1207, "k": "Canada", "w": "November"},
    {"n": "Sao_Paulo", "c": "South America", "lat": -23.5505, "lon": -46.6333, "k": "Brazil", "w": "January"},
    {"n": "Buenos_Aires", "c": "South America", "lat": -34.6037, "lon": -58.3816, "k": "Argentina", "w": "February"},
    {"n": "Lima", "c": "South America", "lat": -12.0464, "lon": -77.0428, "k": "Peru", "w": "February"},
    {"n": "Bogota", "c": "South America", "lat": 4.711, "lon": -74.0721, "k": "Colombia", "w": "April"},
    {"n": "Santiago", "c": "South America", "lat": -33.4489, "lon": -70.6693, "k": "Chile", "w": "June"},
    {"n": "Quito", "c": "South America", "lat": -0.1807, "lon": -78.4678, "k": "Ecuador", "w": "April"},
    {"n": "Manaus", "c": "South America", "lat": -3.119, "lon": -60.0217, "k": "Brazil", "w": "March"},
    {"n": "Sydney", "c": "Oceania", "lat": -33.8688, "lon": 151.2093, "k": "Australia", "w": "February"},
    {"n": "Melbourne", "c": "Oceania", "lat": -37.8136, "lon": 144.9631, "k": "Australia", "w": "October"},
    {"n": "Auckland", "c": "Oceania", "lat": -36.8509, "lon": 174.7645, "k": "New Zealand", "w": "July"}
]

ANTARCTICA_CITY: Dict = {
    "n": "Antarctica",
    "c": "Antarctica",
    "lat": -80.0,
    "lon": 0.0,
    "k": "Antarctica",
    "w": "n/a",
    "city": "Antarctica",
    "name": "Antarctica",
    "continent": "Antarctica",
    "latitude": -80.0,
    "longitude": 0.0,
    "country": "Antarctica",
    "wettest_month": "n/a",
    "is_antarctica": True,
    "soil_moisture_na": True,
    "soil_moisture_reason": "no soil-moisture data over ice"
}

def normalize_key(value: Optional[str]) -> str:
    return str(value or "").replace("_", "").replace("-", "").replace(" ", "").lower()

CITIES: List[Dict] = []
CITY_MAP: Dict[str, Dict] = {}

for item in RAW_CITIES:
    canonical = {
        "city": item["n"],
        "name": item["n"],
        "continent": item["c"],
        "latitude": item["lat"],
        "longitude": item["lon"],
        "country": item["k"],
        "wettest_month": item["w"],
        "n": item["n"],
        "c": item["c"],
        "lat": item["lat"],
        "lon": item["lon"],
        "k": item["k"],
        "w": item["w"],
        "is_antarctica": False
    }
    CITIES.append(canonical)
    key = normalize_key(item["n"])
    CITY_MAP[key] = canonical

# Register Antarctica
CITY_MAP[normalize_key("Antarctica")] = ANTARCTICA_CITY
CITY_MAP[normalize_key("McMurdo")] = ANTARCTICA_CITY

def get_cities(include_antarctica: bool = True) -> List[Dict]:
    if include_antarctica:
        return CITIES + [ANTARCTICA_CITY]
    return list(CITIES)

def get_city(name: str) -> Optional[Dict]:
    key = normalize_key(name)
    return CITY_MAP.get(key)
