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

stations = {'Centar': '42.0012,21.4288', 'GaziBaba': '42.0368,21.508', 'Karpos': '42.0066,21.3954',
            'Lisice': '41.9753,21.4917', 'Mrsevci': '42.0167,21.6525', 'Miladinovci': '41.9803,21.6498',
            'Kocani': '41.9164,22.4128', 'Kavadarci': '41.4331,22.0119', 'Kumanovo': '42.1322,21.7144',
            'Kicevo': '41.5261,20.9462', 'Lazaropole': '41.536,20.695', 'Tetovo': '42.0106,20.9714'}
pollutants = ['CO', 'NO2', 'O3', 'PM25', 'PM10', 'SO2', 'CO2', 'AQI']
