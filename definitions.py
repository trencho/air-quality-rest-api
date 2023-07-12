from os import environ, path

APP_ENV = "APP_ENV"

DARK_SKY_TOKEN = "DARK_SKY_TOKEN"

GITHUB_TOKEN = "GITHUB_TOKEN"

MONGO_DATABASE = "MONGO_DATABASE"
MONGO_PASSWORD = "MONGO_PASSWORD"
MONGO_USERNAME = "MONGO_USERNAME"
MONGODB_CONNECTION = "MONGODB_CONNECTION"
MONGODB_HOSTNAME = "MONGODB_HOSTNAME"

OPEN_WEATHER_TOKEN = "OPEN_WEATHER_TOKEN"

REPO_NAME = "REPO_NAME"

VOLUME_PATH = "VOLUME_PATH"

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

URL_PREFIX = "/api/v1"

ROOT_PATH = environ.get(VOLUME_PATH, "") or path.dirname(path.abspath(__file__))

DATA_PATH = path.join(ROOT_PATH, "data")
DATA_EXTERNAL_PATH = path.join(DATA_PATH, "external")
DATA_PROCESSED_PATH = path.join(DATA_PATH, "processed")
DATA_RAW_PATH = path.join(DATA_PATH, "raw")

LOG_PATH = path.join(ROOT_PATH, "logs")

MODELS_PATH = path.join(ROOT_PATH, "models")

RESULTS_PATH = path.join(ROOT_PATH, "results")
RESULTS_ERRORS_PATH = path.join(RESULTS_PATH, "errors")
RESULTS_PREDICTIONS_PATH = path.join(RESULTS_PATH, "predictions")

APP_DEV = "development"
APP_PROD = "production"

COLLECTIONS = ["weather", "pollution"]

CHUNK_SIZE = 15000

COUNTRIES = {
    "MK": "Macedonia"
}

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
    "DecisionTreeRegressionModel": "Decision Tree",
    "LightGBMRegressionModel": "LightGBM",
    "LinearRegressionModel": "Linear",
    "MLPRegressionModel": "Multilayer Perceptron",
    # "RandomForestRegressionModel": "Random Forest",
    "SupportVectorRegressionModel": "Support Vector",
    "XGBoostRegressionModel": "XGBoost"
}

FORECAST_COUNTER = "forecast_counter"
ONECALL_COUNTER = "onecall_counter"
REQUESTS_LIMIT = 1000
