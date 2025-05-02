import seaborn
from matplotlib import pyplot
from pandas import DataFrame, read_csv

from definitions import POLLUTANTS, REGRESSION_MODELS, RESULTS_ERRORS_PATH
from .handle_plot import save_plot

ERROR_TYPES = {
    "mae": "Mean Absolute Error",
    "mape": "Mean Absolute Percentage Error",
    "mse": "Mean Squared Error",
    "rmse": "Root Mean Squared Error",
}

PLOT_PARAMS = {
    "legend.fontsize": 16,
    "figure.figsize": (16, 10),
    "axes.labelsize": 16,
    "axes.titlesize": 16,
    "xtick.labelsize": 16,
    "ytick.labelsize": 16,
    "figure.titlesize": 22,
    "xtick.major.pad": 8,
}


def draw_errors(city: dict, sensor: dict, pollutant: str) -> None:
    pyplot.rcParams.update(PLOT_PARAMS)
    pyplot.style.use("seaborn-v0_8-whitegrid")
    seaborn.set_style("white")

    for error_key, error_val in ERROR_TYPES.items():
        data = []
        for model_name in REGRESSION_MODELS:
            dataframe_errors = read_csv(
                RESULTS_ERRORS_PATH
                / "data"
                / city["cityName"]
                / sensor["sensorId"]
                / pollutant
                / model_name
                / "error.csv"
            )
            data.append(
                [REGRESSION_MODELS[model_name], dataframe_errors.iloc[0][error_val]]
            )

        dataframe_algorithms = DataFrame(
            data, columns=["algorithm", pollutant]
        ).dropna()
        if dataframe_algorithms.empty:
            continue

        dataframe_algorithms = dataframe_algorithms.sort_values(
            by=pollutant, ascending=False
        ).reset_index(drop=True)

        fig, ax = pyplot.subplots(figsize=(16, 10), facecolor="white", dpi=80)
        ax.vlines(
            x=dataframe_algorithms.index,
            ymin=0,
            ymax=dataframe_algorithms[pollutant],
            color="firebrick",
            alpha=0.7,
            linewidth=40,
            label=POLLUTANTS[pollutant],
        )
        ax.legend()

        for i, value in enumerate(dataframe_algorithms[pollutant]):
            ax.text(
                i,
                value + 0.5,
                round(value, 1),
                fontsize=22,
                horizontalalignment="center",
            )

        ax.set_title(
            f"{city['siteName']} - {sensor['description']}", fontdict={"size": 22}
        )
        ax.set_ylabel(error_val, fontsize=22)
        y_lim = (
            dataframe_algorithms[pollutant].max()
            + 10
            - (dataframe_algorithms[pollutant].max() % 10)
        )
        ax.set_ylim(ymin=0, ymax=y_lim)
        pyplot.xticks(
            dataframe_algorithms.index,
            dataframe_algorithms["algorithm"],
            horizontalalignment="center",
            fontsize=22,
            rotation=30,
        )

        save_plot(
            fig,
            pyplot,
            RESULTS_ERRORS_PATH
            / "plots"
            / city["cityName"]
            / sensor["sensorId"]
            / pollutant,
            error_key,
        )
