from pandas import DataFrame, Series
from statsmodels.api import add_constant, OLS


def get_p_values(x: DataFrame, y: Series, features: list) -> Series:
    features_with_constant = add_constant(x[features], has_constant="add")
    model = OLS(y, features_with_constant).fit()
    return Series(model.pvalues[1:], index=features)


def backward_elimination(
    x: DataFrame, y: Series, significance_level: float = 0.05
) -> list:
    features = x.columns.values.tolist()
    while len(features) > 0:
        p_values = get_p_values(x, y, features)
        if max(p_values) > significance_level:
            feature_with_p_max = p_values.idxmax()
            features.remove(feature_with_p_max)
        else:
            break
    return features
