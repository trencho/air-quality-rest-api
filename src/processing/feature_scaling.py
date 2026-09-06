from pandas import DataFrame
from sklearn.base import TransformerMixin
from sklearn.preprocessing import MinMaxScaler, RobustScaler, StandardScaler

SCALERS = {
    "min_max": MinMaxScaler,
    "standard": StandardScaler,
    "robust": RobustScaler,
}


def _as_frame(values, template: DataFrame) -> DataFrame:
    return DataFrame(values, template.index, template.columns)


def fit_scaler(
    dataframe: DataFrame, scale: str = "robust"
) -> tuple[DataFrame, TransformerMixin]:
    """Fit a scaler on this frame and return the scaled frame alongside it.

    The ONLY place `fit_transform` appears in this codebase, so "nothing fits outside fit_scaler"
    is a one-line check rather than a convention.

    This replaces a single `value_scaling` that always fitted and was called from training AND from
    the forecast loop, so the scaler serving a request was fitted on that request's own frame.
    Training also scaled the WHOLE frame before splitting off the validation quarter, which put the
    test rows' statistics into the scaler the model was fitted under.

    It also held the three scalers as module-level INSTANCES in a dict, so any caller naming a
    scaler shared one mutable object with every other caller - and training spawns a thread per
    (city, sensor, pollutant). Nothing named one in production, so that was a trap rather than a
    live bug, but the class-per-entry here means it cannot become one.
    """
    scaler = SCALERS.get(scale, RobustScaler)()
    return _as_frame(scaler.fit_transform(dataframe), dataframe), scaler


def apply_scaler(dataframe: DataFrame, scaler: TransformerMixin) -> DataFrame:
    """Scale with an already-fitted scaler. No `fit` in this function, deliberately."""
    return _as_frame(scaler.transform(dataframe), dataframe)
