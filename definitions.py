from os import path

ROOT_DIR = path.dirname(path.abspath(__file__))

DATA_PATH = path.join(ROOT_DIR, 'data')
DATA_EXTERNAL_PATH = path.join(DATA_PATH, 'external')
DATA_INTERIM_PATH = path.join(DATA_PATH, 'interim')
DATA_PROCESSED_PATH = path.join(DATA_PATH, 'processed')
DATA_RAW_PATH = path.join(DATA_PATH, 'raw')

MODELS_PATH = path.join(ROOT_DIR, 'models')

RESULTS_PATH = path.join(ROOT_DIR, 'results')
RESULTS_ERRORS_PATH = path.join(RESULTS_PATH, 'errors')
RESULTS_PREDICTIONS_PATH = path.join(RESULTS_PATH, 'predictions')

SRC_PATH = path.join(ROOT_DIR, 'src')
SRC_DATA_PATH = path.join(SRC_PATH, 'data')
SRC_MODELING_PATH = path.join(SRC_PATH, 'modeling')
SRC_MODELS_PATH = path.join(SRC_PATH, 'models')
SRC_PREPARATION_PATH = path.join(SRC_PATH, 'preparation')
SRC_PROCESSING_PATH = path.join(SRC_PATH, 'processing')

HTTP_BAD_REQUEST = 400
HTTP_NOT_FOUND = 404

dark_sky_env_value = 'DARK_SKY_CREDENTIALS'
pulse_eco_env_value = 'PULSE_ECO_CREDENTIALS'

github_token_env_value = 'GITHUB_TOKEN'

mongodb_host_env_value = 'MONGODB_HOSTNAME'
mongodb_name_env_value = 'MONGODB_DATABASE'
mongodb_user_name_env_value = 'MONGODB_USERNAME'
mongodb_user_pass_env_value = 'MONGODB_PASSWORD'

environment_variables = [
    dark_sky_env_value,
    pulse_eco_env_value,
    github_token_env_value,
    mongodb_user_name_env_value,
    mongodb_user_pass_env_value,
    mongodb_host_env_value,
    mongodb_name_env_value
]

OPEN_API_VERSION = '3.0.3'

pollutants = {
    'co': 'CO',
    'no2': 'NO2',
    'o3': 'O3',
    'pm25': 'PM2.5',
    'pm10': 'PM10',
    'so2': 'SO2',
    'co2': 'CO2',
    'aqi': 'AQI'
}

collections = [
    'weather',
    'pollution',
    'summary'
]

regression_models = {
    'DecisionTreeRegressionModel': 'Decision Tree',
    'DummyRegressionModel': 'Dummy',
    'LightGBMRegressionModel': 'LightGBM',
    'LinearRegressionModel': 'Linear',
    'MLPRegressionModel': 'Multilayer Perceptron',
    'RandomForestRegressionModel': 'Random Forest',
    'SupportVectorRegressionModel': 'Support Vector',
    'TPOTRegressionModel': 'TPOT',
    'XGBoostRegressionModel': 'XGBoost'
}

hour_in_secs = 3600
