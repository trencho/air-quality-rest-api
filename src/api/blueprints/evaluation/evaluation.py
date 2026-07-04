from typing import Optional

from flasgger import swag_from
from flask import Blueprint, jsonify, Response
from pandas import isna, read_csv
from starlette.status import HTTP_404_NOT_FOUND

from api.config.cache import cache
from api.config.converters import PollutantType
from definitions import CACHE_TIMEOUTS, MODELS_PATH, POLLUTANTS, RESULTS_ERRORS_PATH
from preparation import check_city, check_sensor

evaluation_blueprint = Blueprint("evaluation", __name__)


def _read_best_model_evaluation(
    city_name: str, sensor_id: str, pollutant: str
) -> Optional[dict]:
    # The forecast is served by the best model saved at the pollutant dir; report that
    # model's held-out error metrics (written per model during training).
    pollutant_dir = MODELS_PATH / city_name / sensor_id / pollutant
    if not (models := list(pollutant_dir.glob("*.mdl"))):
        return None

    model_name = models[0].stem
    error_file = (
        RESULTS_ERRORS_PATH
        / "data"
        / city_name
        / sensor_id
        / pollutant
        / model_name
        / "error.csv"
    )
    if not error_file.exists():
        return None

    row = read_csv(error_file).iloc[0]
    return {
        "model": model_name,
        "metrics": {
            column: (None if isna(value) else float(value))
            for column, value in row.items()
        },
    }


@evaluation_blueprint.get(
    "/cities/<string:city_name>/sensors/<string:sensor_id>/evaluation/",
    endpoint="city_sensor",
)
@cache.memoize(timeout=CACHE_TIMEOUTS["1h"])
@swag_from(
    "evaluation_city_sensor.yml", endpoint="evaluation.city_sensor", methods=["GET"]
)
def fetch_sensor_evaluation(
    city_name: str, sensor_id: str
) -> Response | tuple[Response, int]:
    if check_city(city_name) is None:
        return (
            jsonify(
                error_message="Cannot return forecast quality because the city is not found or is invalid."
            ),
            HTTP_404_NOT_FOUND,
        )

    if check_sensor(city_name, sensor_id) is None:
        return (
            jsonify(
                error_message="Cannot return forecast quality because the sensor is not found or is invalid."
            ),
            HTTP_404_NOT_FOUND,
        )

    results = {}
    for pollutant in POLLUTANTS:
        if (
            evaluation := _read_best_model_evaluation(city_name, sensor_id, pollutant)
        ) is not None:
            results[pollutant] = evaluation

    return jsonify(results)


@evaluation_blueprint.get(
    "/cities/<string:city_name>/sensors/<string:sensor_id>/pollutants/"
    "<pollutant_type:pollutant>/evaluation/",
    endpoint="city_sensor_pollutant",
)
@cache.memoize(timeout=CACHE_TIMEOUTS["1h"])
@swag_from(
    "evaluation_city_sensor_pollutant.yml",
    endpoint="evaluation.city_sensor_pollutant",
    methods=["GET"],
)
def fetch_pollutant_evaluation(
    city_name: str, sensor_id: str, pollutant: PollutantType
) -> Response | tuple[Response, int]:
    if check_city(city_name) is None:
        return (
            jsonify(
                error_message="Cannot return forecast quality because the city is not found or is invalid."
            ),
            HTTP_404_NOT_FOUND,
        )

    if check_sensor(city_name, sensor_id) is None:
        return (
            jsonify(
                error_message="Cannot return forecast quality because the sensor is not found or is invalid."
            ),
            HTTP_404_NOT_FOUND,
        )

    if (
        evaluation := _read_best_model_evaluation(city_name, sensor_id, pollutant)
    ) is None:
        return (
            jsonify(
                error_message="Cannot return forecast quality because no trained model exists for that pollutant."
            ),
            HTTP_404_NOT_FOUND,
        )

    return jsonify(evaluation)
