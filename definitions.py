from os import environ
from pathlib import Path

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

ENVIRONMENT_VARIABLES = [
    APP_ENV,
    GITHUB_TOKEN,
    MONGO_DATABASE,
    MONGO_PASSWORD,
    MONGO_USERNAME,
    MONGODB_CONNECTION,
    MONGODB_HOSTNAME,
    OPEN_WEATHER_TOKEN,
    REPO_NAME
]

VOLUME_PATH = "VOLUME_PATH"
ROOT_PATH = environ.get(VOLUME_PATH, "") or Path(__file__).resolve().parent
DATA_PATH = ROOT_PATH / "data"
LOG_PATH = ROOT_PATH / "logs"
MODELS_PATH = ROOT_PATH / "models"
RESULTS_PATH = ROOT_PATH / "results"

DATA_EXTERNAL_PATH = DATA_PATH / "external"
DATA_PROCESSED_PATH = DATA_PATH / "processed"
DATA_RAW_PATH = DATA_PATH / "raw"

RESULTS_ERRORS_PATH = RESULTS_PATH / "errors"
RESULTS_ERRORS_PLOTS_PATH = RESULTS_ERRORS_PATH / "plots"
RESULTS_PREDICTIONS_PATH = RESULTS_PATH / "predictions"
RESULTS_PREDICTIONS_PLOTS_PATH = RESULTS_PREDICTIONS_PATH / "plots"

ENV_DEV = "development"
ENV_PROD = "production"

COLLECTIONS = ["weather", "pollution"]
CHUNK_SIZE = 15000

CACHE_TIMEOUTS = {
    "never": 0,
    "1min": 60,
    "3min": 180,
    "5min": 300,
    "1h": 3600
}

COUNTRIES = {"MK": "Macedonia"}
POLLUTANTS = {
    "aqi": "AQI",
    "co": "CO",
    "nh3": "NH3",
    "no": "NO",
    "no2": "NO2",
    "o3": "O3",
    "pm2_5": "PM2.5",
    "pm10": "PM10",
    "so2": "SO2"
}

REGRESSION_MODELS = {
    # "DecisionTreeRegressionModel": "Decision Tree",
    "LightGBMRegressionModel": "LightGBM",
    # "LinearRegressionModel": "Linear",
    # "MLPRegressionModel": "Multilayer Perceptron",
    "RandomForestRegressionModel": "Random Forest",
    # "SupportVectorRegressionModel": "Support Vector",
    "XGBoostRegressionModel": "XGBoost"
}

URL_PREFIX = "/api/v1"
