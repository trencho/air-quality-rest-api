from os import path

ROOT_DIR = path.dirname(path.abspath(__file__))

DATA_PATH = path.join(ROOT_DIR, 'data')
DATA_EXTERNAL_PATH = path.join(DATA_PATH, 'external')
DATA_PROCESSED_PATH = path.join(DATA_PATH, 'processed')
DATA_RAW_PATH = path.join(DATA_PATH, 'raw')

MODELS_PATH = path.join(ROOT_DIR, 'models')

RESULTS_PATH = path.join(ROOT_DIR, 'results')
RESULTS_ERRORS_PATH = path.join(RESULTS_PATH, 'errors')
RESULTS_PREDICTIONS_PATH = path.join(RESULTS_PATH, 'predictions')

app_env = 'APP_ENV'
app_name = 'APP_NAME'

github_token = 'GITHUB_TOKEN'
open_weather_token = 'OPEN_WEATHER_TOKEN'

mongodb_connection = 'MONGODB_CONNECTION'
mongodb_username = 'MONGODB_USERNAME'
mongodb_password = 'MONGODB_PASSWORD'
mongodb_hostname = 'MONGODB_HOSTNAME'
mongodb_db_name = 'MONGODB_DATABASE'

environment_variables = [
    app_env,
    app_name,
    github_token,
    open_weather_token,
    mongodb_connection,
    mongodb_username,
    mongodb_password,
    mongodb_hostname,
    mongodb_db_name
]

app_dev = 'development'
app_prod = 'production'

collections = ['weather', 'pollution', 'summary']

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
    'DummyRegressionModel': 'Dummy',
    'LightGBMRegressionModel': 'LightGBM',
    'LinearRegressionModel': 'Linear',
    'MLPRegressionModel': 'Multilayer Perceptron',
    # 'RandomForestRegressionModel': 'Random Forest',
    'SupportVectorRegressionModel': 'Support Vector',
    # 'TPOTRegressionModel': 'TPOT',
    'XGBoostRegressionModel': 'XGBoost'
}
