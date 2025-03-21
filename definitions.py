from os import environ, path

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

# Constants for paths
VOLUME_PATH = "VOLUME_PATH"
ROOT_PATH = environ.get(VOLUME_PATH, "") or path.dirname(path.abspath(__file__))
DATA_PATH = path.join(ROOT_PATH, "data")
LOG_PATH = path.join(ROOT_PATH, "logs")
MODELS_PATH = path.join(ROOT_PATH, "models")
RESULTS_PATH = path.join(ROOT_PATH, "results")

# Constants for data paths
DATA_EXTERNAL_PATH = path.join(DATA_PATH, "external")
DATA_PROCESSED_PATH = path.join(DATA_PATH, "processed")
DATA_RAW_PATH = path.join(DATA_PATH, "raw")

# Constants for results paths
RESULTS_ERRORS_PATH = path.join(RESULTS_PATH, "errors")
RESULTS_ERRORS_PLOTS_PATH = path.join(RESULTS_ERRORS_PATH, "plots")
RESULTS_PREDICTIONS_PATH = path.join(RESULTS_PATH, "predictions")
RESULTS_PREDICTIONS_PLOTS_PATH = path.join(RESULTS_PREDICTIONS_PATH, "plots")

# Constants for environment
ENV_DEV = "development"
ENV_PROD = "production"

# Constants for collections and chunk size
COLLECTIONS = ["weather", "pollution"]
CHUNK_SIZE = 15000

CACHE_TIMEOUTS = {
    "never": 0,
    "1min": 60,
    "3min": 180,
    "5min": 300,
    "1h": 3600
}

# Constants for countries and pollutants
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

# Constants for regression models
REGRESSION_MODELS = {
    # "DecisionTreeRegressionModel": "Decision Tree",
    "LightGBMRegressionModel": "LightGBM",
    # "LinearRegressionModel": "Linear",
    # "MLPRegressionModel": "Multilayer Perceptron",
    "RandomForestRegressionModel": "Random Forest",
    # "SupportVectorRegressionModel": "Support Vector",
    "XGBoostRegressionModel": "XGBoost"
}

# URL prefix for API
URL_PREFIX = "/api/v1"
