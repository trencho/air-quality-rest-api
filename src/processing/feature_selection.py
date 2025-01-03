from pandas import Series
from statsmodels.api import add_constant, OLS

# Constants
SIGNIFICANCE_LEVEL = 0.05


def get_p_values(x, y, features):
    features_with_constant = add_constant(x[features], has_constant="add")
    model = OLS(y, features_with_constant).fit()
    return Series(model.pvalues[1:], index=features)


def backward_elimination(x, y: Series, significance_level: float = SIGNIFICANCE_LEVEL) -> list:
    features = x.columns.values.tolist()
    while len(features) > 0:
        p_values = get_p_values(x, y, features)
        if max(p_values) > significance_level:
            feature_with_p_max = p_values.idxmax()
            features.remove(feature_with_p_max)
        else:
            break
    return features
