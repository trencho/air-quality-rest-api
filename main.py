from os import path
from threading import Thread

import joblib
import pandas as pd
import pymongo
from flask import Flask, request, jsonify

from definitions import MODELS_PATH, stations, pollutants, DATA_RAW_PATH
from src.modeling import train_model
from src.preparation import weather_data_api

app = Flask(__name__)
app.config["MONGO_URI"] = "mongodb://localhost:27017/local"
mongo = pymongo

HTTP_BAD_REQUEST = 400


@app.route('/fetchPollutionData')
def fetch_pollution_data():
    pass


@app.route('/fetchWeatherData')
def fetch_weather_data():
    station = request.args.get('station', default=None, type=str)
    timestamp = request.args.get('timestamp', default=None, type=float)
    if station not in stations:
        message = 'Cannot fetch data because the station is invalid.'
        response = jsonify(status='error', error_message=message)
        # Sets the status code to 400
        response.status_code = HTTP_BAD_REQUEST
        return response

    if timestamp is None:
        message = 'Cannot fetch data because the starting timestamp is missing.'
        response = jsonify(status='error', error_message=message)
        # Sets the status code to 400
        response.status_code = HTTP_BAD_REQUEST
        return response

    weather_data_api(station, timestamp)
    message = 'Fetched weather data from the Dark Sky API.'
    response = jsonify(status='complete', label=message)
    return response


@app.route('/forecast')
def forecast():
    station = request.args.get('station', default=None, type=str)
    measurement = request.args.get('measurement', default=None, type=str)
    if station is None or measurement is None:
        message = 'Cannot return data because the station or measurement is missing.'
        response = jsonify(status='error', error_message=message)
        # Sets the status code to 400
        response.status_code = HTTP_BAD_REQUEST
        return response

    dataset = pd.read_csv(DATA_RAW_PATH + '/combined/combined_report_' + station + '.csv')
    dataset['time'] = dataset['time'] * 1000
    return dataset[['time', measurement]].to_json(orient='values')


@app.route('/predict')
def predict():
    station = request.args.get('station', default=None, type=str)
    pollutant = request.args.get('pollutant', default=None, type=str)
    if station not in stations:
        message = 'Record cannot be scored because the station is missing or is invalid.'
        response = jsonify(status='error', error_message=message)
        # Sets the status code to 400
        response.status_code = HTTP_BAD_REQUEST
        return response

    if pollutant not in pollutants:
        message = 'Record cannot be scored because the pollutant is missing or is invalid.'
        response = jsonify(status='error', error_message=message)
        # Sets the status code to 400
        response.status_code = HTTP_BAD_REQUEST
        return response

    if not path.exists(MODELS_PATH + '/' + station + '/' + pollutant + '/best_regression_model.pkl'):
        train_model.train(station, pollutant)
        message = 'Value cannot be predicted because the model is not trained. Try again later.'
        response = jsonify(status='error', error_message=message)
        # Sets the status code to 400
        response.status_code = HTTP_BAD_REQUEST
        return response

    model = joblib.load(MODELS_PATH + '/' + station + '/' + pollutant + '/best_regression_model.pkl')
    with open(MODELS_PATH + '/' + station + '/' + pollutant + '/selected_features.txt', 'r') as in_file:
        model_features = in_file.read()
    features = []
    for model_feature in model_features:
        feature = request.args.get(model_feature, default=None, type=str)
        # Reject request that have bad or missing values
        if feature is None:
            message = ('Record cannot be scored because of missing or unacceptable values. '
                       'All values must be present and of type float.')
            response = jsonify(status='error', error_message=message, missing=feature)
            # Sets the status code to 400
            response.status_code = HTTP_BAD_REQUEST
            return response
        else:
            features.append(feature)

    prediction = round(model.predict(features)[0])
    return jsonify(status='complete', value=prediction)


@app.route('/train')
def train():
    # TODO: Extend with newer database entries for weather and pollution
    station = request.args.get('station', default=None, type=str)
    pollutant = request.args.get('pollutant', default=None, type=str)
    if (station is not None and station not in stations) or (
            pollutant is not None and pollutant not in pollutants):
        message = 'Record cannot be scored because the station or value type is missing.'
        response = jsonify(status='error', error_message=message)
        # Sets the status code to 400
        response.status_code = HTTP_BAD_REQUEST
        return response

    Thread(target=train_model.train, args=(station, pollutant)).start()
    return jsonify(status='start', label='Training initialized...')


if __name__ == '__main__':
    app.run(debug=True)
