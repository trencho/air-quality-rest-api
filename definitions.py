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

HTTP_BAD_REQUEST = 400
HTTP_NOT_FOUND = 404

dark_sky_token_env_value = 'DARK_SKY_TOKEN'
pulse_eco_user_name_env_value = 'PULSE_ECO_USER_NAME_CREDENTIALS'
pulse_eco_user_pass_env_value = 'PULSE_ECO_USER_PASS_CREDENTIALS'

github_token_env_value = 'GITHUB_TOKEN'

mongodb_host_env_value = 'MONGODB_HOSTNAME'
mongodb_name_env_value = 'MONGODB_DATABASE'
mongodb_user_name_env_value = 'MONGODB_USERNAME'
mongodb_user_pass_env_value = 'MONGODB_PASSWORD'

environment_variables = [
    dark_sky_token_env_value,
    pulse_eco_user_name_env_value,
    pulse_eco_user_pass_env_value,
    github_token_env_value,
    mongodb_user_name_env_value,
    mongodb_user_pass_env_value,
    mongodb_host_env_value,
    mongodb_name_env_value
]

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
