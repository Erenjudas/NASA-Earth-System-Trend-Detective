# Be An Earth System Trend Detective 🌍

## Project Overview

**Be An Earth System Trend Detective** is a data science project developed for the NASA Space Apps Challenge 2026.

The project analyzes long-term precipitation and root-zone soil moisture trends across selected cities around the world using NASA POWER environmental data.

It identifies increasing and decreasing environmental trends, detects opposite trends between cities, groups locations with similar environmental patterns, compares selected cities, and generates indicative future projections.

## Data Source

This project uses monthly environmental data from the **NASA POWER API**.

### Environmental Variables

- **PRECTOTCORR:** Corrected precipitation (mm/day).
- **GWETROOT:** Root-zone soil moisture (0–1).

### Data Coverage

- 39 selected cities
- 6 continents
- 1981–2025
- 540 monthly observations per city
- 21,060 monthly records in total

## Data Science Methodology

### 1. Data Collection and Cleaning

- Collect monthly environmental data from NASA POWER.
- Handle missing and invalid values.
- Remove duplicate records.
- Validate monthly observations.
- Prepare clean datasets for statistical analysis.

### 2. Statistical Trend Analysis

- Calculate annual averages.
- Apply the Mann-Kendall trend test.
- Estimate Sen's slope.
- Calculate percentage change per decade.
- Identify statistically significant increasing and decreasing trends.
- Validate statistical results using independent calculations.

### 3. Forecasting

- Use Linear Regression with monthly seasonal features.
- Train models using historical data from 1981–2020.
- Evaluate predictions on 2021–2025 data.
- Generate indicative monthly projections for 2026–2035.
- Calculate MAE and RMSE.
- Compare model performance with a seasonal-naive baseline.
- Generate model-based prediction intervals.

**Note:** These are indicative long-term projections, not operational weather forecasts.

### 4. Opposite Trend Detection

- Identify city pairs with statistically significant opposite trends.
- Compare increasing and decreasing trends for the same environmental variable.
- Rank city pairs according to their trend gaps.
- Avoid repeating cities across selected pairs.

### 5. City Clustering

- Apply StandardScaler and K-Means clustering.
- Group cities based on precipitation and soil moisture trends.
- Evaluate different cluster numbers using silhouette scores.
- Generate cluster assignments and cluster centers.

### 6. Manual Statistical Validation

- Independently implement Mann-Kendall calculations.
- Independently calculate Sen's slope.
- Compare independent results against the PyMannKendall library.
- Generate a statistical validation report.

### 7. City Comparison

- Compare selected cities using historical monthly observations.
- Compare annual precipitation and soil moisture trends.
- Compare indicative future projections.
- Generate comparison CSV files and visualizations.

## Technologies Used

- Python 3.11
- Pandas
- NumPy
- Matplotlib
- Seaborn
- SciPy
- Scikit-learn
- Statsmodels
- PyMannKendall
- NASA POWER API
- Pytest

## Project Structure

```text
NASA_Earth_System_Trend_Detective/
│
├── data/
│   ├── raw/
│   ├── processed/
│   └── cache/
│
├── notebooks/
│
├── src/
│   ├── __init__.py
│   ├── data_collection.py
│   ├── data_cleaning.py
│   ├── statistics_analysis.py
│   ├── forecasting.py
│   ├── clustering.py
│   ├── opposite_trends.py
│   ├── manual_validation.py
│   ├── city_comparison.py
│   └── city_comparison_visualization.py
│
├── outputs/
│   ├── monthly_forecasts/
│   ├── city_comparisons/
│   ├── all_cities_annual_averages.csv
│   ├── all_cities_trend_results.csv
│   ├── monthly_10_year_forecasts.csv
│   ├── monthly_forecast_evaluation_report.csv
│   ├── opposite_trends.csv
│   ├── city_clusters.csv
│   ├── cluster_centers.csv
│   └── manual_validation_report.csv
│
├── tests/
│   ├── test_data_cleaning.py
│   ├── test_statistics_analysis.py
│   ├── test_forecasting.py
│   ├── test_clustering.py
│   └── test_opposite_trends.py
│
├── config.py
├── main.py
├── requirements.txt
├── .gitignore
└── README.md
```

## Installation and Setup

### 1. Clone the Repository

```bash
git clone https://github.com/hab7666/NASA-Earth-System-Trend-Detective.git
cd NASA-Earth-System-Trend-Detective
```

### 2. Create a Virtual Environment

```bash
python -m venv venv
```

### 3. Activate the Virtual Environment

Windows PowerShell:

```powershell
.\venv\Scripts\Activate.ps1
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

## Run the Web App Locally

The FastAPI server serves both the frontend and backend API. From the project folder, start it with:

```powershell
python -m uvicorn app:app --host 127.0.0.1 --port 8000
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000) in your browser. The API documentation is available at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs). Stop the server with `Ctrl+C`.

## Running the Project

### Run Statistical Analysis and Machine Learning Modules

```bash
python main.py --analysis
```

### Run the Complete Pipeline

```bash
python main.py --all
```

The complete pipeline includes data collection, cleaning, and subsequent analysis stages.

## Running Automated Tests

The project includes automated tests for data cleaning, statistical analysis, forecasting, clustering, and opposite trend detection.

Run all tests:

```bash
python -m pytest -v
```

Run a specific test module:

```bash
python -m pytest tests/test_forecasting.py -v
```

### Current Testing Results

**45 automated tests passed successfully.**

| Test Module | Tests Passed |
|---|---:|
| Data Cleaning | 10/10 |
| Statistical Analysis | 8/8 |
| Forecasting | 10/10 |
| Clustering | 8/8 |
| Opposite Trend Detection | 9/9 |
| **Total** | **45/45** |

## Important Output Files

The project generates CSV reports and visualizations.

### Statistical Analysis

- `all_cities_annual_averages.csv`
- `all_cities_trend_results.csv`
- `statistics_library_validation_report.csv`

### Forecasting

- `monthly_10_year_forecasts.csv`
- `monthly_forecast_evaluation_report.csv`
- `monthly_forecast_test_predictions.csv`

### Clustering

- `city_clusters.csv`
- `cluster_centers.csv`
- `clustering_metrics.csv`
- `clustering_evaluation.png`

### Opposite Trend Detection

- `opposite_trends.csv`

### Manual Validation

- `manual_validation_report.csv`

### City Comparison

- Historical and forecast comparison CSV files.
- Monthly and annual comparison graphs.
- Future precipitation and soil moisture projections.

## Important Limitations

- The analysis covers 39 selected cities, not every location on Earth.
- Forecasts are indicative long-term projections, not operational weather forecasts.
- Forecast accuracy varies across cities and environmental variables.
- Statistical significance does not establish causation.
- Model-based prediction intervals do not capture all sources of climate uncertainty.
- NASA POWER data are gridded/model-assisted estimates and should not be interpreted as direct ground-station measurements.

## Team Collaboration

The project is maintained in a shared GitHub repository.

Repository:

https://github.com/hab7666/NASA-Earth-System-Trend-Detective

Team members can clone the repository to access the latest source code, datasets available in the repository, automated tests, and generated analysis outputs.

To get the latest changes:

```bash
git pull origin main
```

## Project Purpose

The goal of this project is to make long-term environmental patterns easier to understand through data science, statistical analysis, forecasting, and machine learning.

By analyzing precipitation and root-zone soil moisture trends across selected cities, the project provides insights into changing environmental patterns and supports data-driven exploration of Earth's changing systems.

---

**NASA Space Apps Challenge 2026**

*Be An Earth System Trend Detective 🌍*