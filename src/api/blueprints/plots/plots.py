from os import path

from flasgger import swag_from
from flask import Blueprint, jsonify, Response, send_file
from starlette.status import HTTP_404_NOT_FOUND

from api.config.converters import ErrorType
from definitions import RESULTS_ERRORS_PLOTS_PATH, RESULTS_PREDICTIONS_PLOTS_PATH
from preparation import check_city, check_sensor

plots_blueprint = Blueprint("plots", __name__)


@plots_blueprint.get("/plots/predictions/cities/<string:city_name>/sensors/<string:sensor_id>/"
                     "pollutants/<pollutant_type:pollutant>/", endpoint="plots_predictions")
@swag_from("plots_predictions.yml", endpoint="plots.plots_predictions", methods=["GET"])
def fetch_plots_predictions(city_name: str, sensor_id: str, pollutant: str) -> Response | tuple[Response, int]:
    if check_city(city_name) is None:
        return jsonify(
            error_message="Cannot return plot because the city is not found or is invalid."), HTTP_404_NOT_FOUND

    if check_sensor(city_name, sensor_id) is None:
        return jsonify(
            error_message="Cannot return plot because the sensor is not found or is invalid."), HTTP_404_NOT_FOUND

    image_path = path.join(RESULTS_PREDICTIONS_PLOTS_PATH, city_name, sensor_id, pollutant, "prediction.png")
    if not path.exists(image_path):
        return jsonify(error_message="Cannot return plot because it does not exist."), HTTP_404_NOT_FOUND

    return send_file(image_path, mimetype="image/png", max_age=3600)


@plots_blueprint.get(
    "/plots/errors/cities/<string:city_name>/sensors/<string:sensor_id>/"
    "pollutants/<pollutant_type:pollutant>/errors/<error_type:error_type>/", endpoint="plots_errors")
@swag_from("plots_errors.yml", endpoint="plots.plots_errors", methods=["GET"])
def fetch_plots_errors(city_name: str, sensor_id: str, pollutant: str, error_type: ErrorType = None) \
        -> Response | tuple[Response, int]:
    if check_city(city_name) is None:
        return jsonify(
            error_message="Cannot return plot because the city is not found or is invalid."), HTTP_404_NOT_FOUND

    if check_sensor(city_name, sensor_id) is None:
        return jsonify(
            error_message="Cannot return plot because the sensor is not found or is invalid."), HTTP_404_NOT_FOUND

    image_path = path.join(RESULTS_ERRORS_PLOTS_PATH, city_name, sensor_id, pollutant)
    match error_type:
        case ErrorType.MEAN_ABSOLUTE_ERROR:
            image_path = image_path.join(f"{ErrorType.MEAN_ABSOLUTE_ERROR.value}.png")
        case ErrorType.MEAN_ABSOLUTE_PERCENTAGE_ERROR:
            image_path = image_path.join(f"{ErrorType.MEAN_ABSOLUTE_PERCENTAGE_ERROR.value}.png")
        case ErrorType.MEAN_SQUARED_ERROR:
            image_path = image_path.join(f"{ErrorType.MEAN_SQUARED_ERROR.value}.png")
        case ErrorType.ROOT_MEAN_SQUARED_ERROR:
            image_path = image_path.join(f"{ErrorType.ROOT_MEAN_SQUARED_ERROR.value}.png")

    if not path.exists(image_path):
        return jsonify(error_message="Cannot return plot because it does not exist."), HTTP_404_NOT_FOUND

    return send_file(image_path, mimetype="image/png", max_age=3600)
