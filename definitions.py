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
    "DecisionTreeRegressionModel": "Decision Tree",
    "LightGBMRegressionModel": "LightGBM",
    "LinearRegressionModel": "Linear",
    "MLPRegressionModel": "Multilayer Perceptron",
    # "RandomForestRegressionModel": "Random Forest",
    "SupportVectorRegressionModel": "Support Vector",
    "XGBoostRegressionModel": "XGBoost"
}

# Constants for counters and request limits
FORECAST_COUNTER = "forecast_counter"
ONECALL_COUNTER = "onecall_counter"
REQUESTS_LIMIT = 1000

# Constants for column data types
COLUMN_DTYPES = {
    "time": int,
    "aqi": float,
    "co": float,
    "no": float,
    "no2": float,
    "o3": float,
    "so2": float,
    "pm2_5": float,
    "pm10": float,
    "nh3": float
}

# URL prefix for API
URL_PREFIX = "/api/v1"
