from os import path

from matplotlib import pyplot
from pandas import DataFrame, DatetimeIndex, read_csv

from definitions import pollutants, regression_models, RESULTS_ERRORS_PATH, RESULTS_PREDICTIONS_PATH
from .handle_plot import save_plot


def draw_predictions(city: dict, sensor: dict, pollutant: str) -> None:
    data = []
    for model_name in regression_models:
        dataframe_errors = read_csv(
            path.join(RESULTS_ERRORS_PATH, "data", city["cityName"], sensor["sensorId"], pollutant, model_name,
                      "error.csv"))
        data.append([model_name, dataframe_errors.iloc[0]["Mean Absolute Error"]])

    dataframe_algorithms = DataFrame(data, columns=["algorithm", pollutant])
    algorithm_index = dataframe_algorithms[pollutant].idxmin()
    dataframe_predictions = read_csv(
        path.join(RESULTS_PREDICTIONS_PATH, "data", city["cityName"], sensor["sensorId"], pollutant,
                  dataframe_algorithms.iloc[algorithm_index]["algorithm"], "prediction.csv"), index_col="time")

    x = DatetimeIndex(dataframe_predictions.index)
    y1 = dataframe_predictions["Actual"]
    y2 = dataframe_predictions["Predicted"]

    fig, ax = pyplot.subplots(1, 1, figsize=(16, 10), dpi=80)
    ax.plot(x, y1, color="tab:red", label="Actual")
    ax.plot(x, y2, color="tab:green",
            label=f"Predicted: {regression_models[dataframe_algorithms.iloc[algorithm_index]['algorithm']]}")

    ax.set_xlabel("Dates", fontsize=22)
    ax.tick_params(axis="x", rotation=0, labelsize=18)
    ax.set_ylabel(f"{pollutants[pollutant]} values", fontsize=22)
    ax.tick_params(axis="y", rotation=0)
    ax.set_title(f"{city['siteName']} - {sensor['description']}", fontsize=22)
    ax.grid(alpha=.4)
    ax.legend(fontsize=16)

    pyplot.gcf().autofmt_xdate()

    save_plot(fig, pyplot,
              path.join(RESULTS_PREDICTIONS_PATH, "plots", city["cityName"], sensor["sensorId"], pollutant),
              "prediction")
