from os import environ, path

app_env = 'APP_ENV'

dark_sky_token = 'DARK_SKY_TOKEN'

github_token = 'GITHUB_TOKEN'

mongo_database = 'MONGO_DATABASE'
mongo_password = 'MONGO_PASSWORD'
mongo_username = 'MONGO_USERNAME'
mongodb_connection = 'MONGODB_CONNECTION'
mongodb_hostname = 'MONGODB_HOSTNAME'

open_weather_token = 'OPEN_WEATHER_TOKEN'

repo_name = 'REPO_NAME'

volume_path = 'VOLUME_PATH'

environment_variables = [
    app_env,
    dark_sky_token,
    github_token,
    mongo_database,
    mongo_password,
    mongo_username,
    mongodb_connection,
    mongodb_hostname,
    open_weather_token,
    repo_name
]

VOLUME_PATH = environ.get(volume_path, '')
ROOT_PATH = VOLUME_PATH or path.dirname(path.abspath(__file__))

DATA_PATH = path.join(ROOT_PATH, 'data')
DATA_EXTERNAL_PATH = path.join(DATA_PATH, 'external')
DATA_PROCESSED_PATH = path.join(DATA_PATH, 'processed')
DATA_RAW_PATH = path.join(DATA_PATH, 'raw')

LOG_PATH = path.join(ROOT_PATH, 'logs')

MODELS_PATH = path.join(ROOT_PATH, 'models')

RESULTS_PATH = path.join(ROOT_PATH, 'results')
RESULTS_ERRORS_PATH = path.join(RESULTS_PATH, 'errors')
RESULTS_PREDICTIONS_PATH = path.join(RESULTS_PATH, 'predictions')

app_dev = 'development'
app_prod = 'production'

collections = ['weather', 'pollution', 'summary']

chunk_size = 10 ** 4

countries = {
    'MK': 'Macedonia'
}

pollutants = {
    'aqi': 'AQI',
    'co': 'CO',
    'nh3': 'NH3',
    'no': 'NO',
    'no2': 'NO2',
    'o3': 'O3',
    'pm2_5': 'PM2.5',
    'pm10': 'PM10',
    'so2': 'SO2'
}

regression_models = {
    'DecisionTreeRegressionModel': 'Decision Tree',
    # 'DummyRegressionModel': 'Dummy',
    'LightGBMRegressionModel': 'LightGBM',
    'LinearRegressionModel': 'Linear',
    'MLPRegressionModel': 'Multilayer Perceptron',
    # 'RandomForestRegressionModel': 'Random Forest',
    'SupportVectorRegressionModel': 'Support Vector',
    # 'TPOTRegressionModel': 'TPOT',
    'XGBoostRegressionModel': 'XGBoost'
}
