"""
Application configuration constants and paths.
This module defines all environment variables and file paths used throughout the application.
"""

from os import environ
from pathlib import Path

# Environment variable keys
APP_ENV = "APP_ENV"
DARK_SKY_TOKEN = "DARK_SKY_TOKEN"
GITHUB_TOKEN = "GITHUB_TOKEN"
MONGO_DATABASE = "MONGO_DATABASE"
MONGO_PASSWORD = "MONGO_PASSWORD"
MONGO_USERNAME = "MONGO_USERNAME"
MONGODB_CONNECTION = "MONGODB_CONNECTION"
MONGODB_HOSTNAME = "MONGODB_HOSTNAME"
OPEN_WEATHER = "open_weather"
OPEN_WEATHER_TOKEN = "OPEN_WEATHER_TOKEN"
REPO_NAME = "REPO_NAME"
VOLUME_PATH = "VOLUME_PATH"

# Environment variable validation list
ENVIRONMENT_VARIABLES = [
    APP_ENV,
    GITHUB_TOKEN,
    MONGO_DATABASE,
    MONGO_PASSWORD,
    MONGO_USERNAME,
    MONGODB_CONNECTION,
    MONGODB_HOSTNAME,
    OPEN_WEATHER_TOKEN,
    REPO_NAME,
]

# Path configuration
ROOT_PATH = Path(environ.get(VOLUME_PATH, str(Path(__file__).resolve().parent)))
DATA_PATH = ROOT_PATH / "data"
LOG_PATH = ROOT_PATH / "logs"
MODELS_PATH = ROOT_PATH / "models"
RESULTS_PATH = ROOT_PATH / "results"

# Data subdirectories
DATA_EXTERNAL_PATH = DATA_PATH / "external"
DATA_PROCESSED_PATH = DATA_PATH / "processed"
DATA_RAW_PATH = DATA_PATH / "raw"

# Results subdirectories
RESULTS_ERRORS_PATH = RESULTS_PATH / "errors"
RESULTS_ERRORS_PLOTS_PATH = RESULTS_ERRORS_PATH / "plots"
RESULTS_PREDICTIONS_PATH = RESULTS_PATH / "predictions"
RESULTS_PREDICTIONS_PLOTS_PATH = RESULTS_PREDICTIONS_PATH / "plots"

# Environment modes
ENV_DEV = "development"
ENV_PROD = "production"

# Data configuration
COLLECTIONS = ["weather", "pollution"]
CHUNK_SIZE = 15000

# Cache timeouts in seconds
CACHE_TIMEOUTS = {
    "never": 0,
    "1min": 60,
    "3min": 180,
    "5min": 300,
    "1h": 3600,
}

# Country configuration
COUNTRIES = {"MK": "Macedonia"}

# Pollutant types and mappings
POLLUTANTS = {
    "aqi": "AQI",
    "co": "CO",
    "nh3": "NH3",
    "no": "NO",
    "no2": "NO2",
    "o3": "O3",
    "pm2_5": "PM2.5",
    "pm10": "PM10",
    "so2": "SO2",
}

# Enabled regression models
REGRESSION_MODELS = {
    "LightGBMRegressionModel": "LightGBM",
    "RandomForestRegressionModel": "Random Forest",
    "XGBoostRegressionModel": "XGBoost",
}

# API configuration
URL_PREFIX = "/api/v1"
