from pandas import Series
from statsmodels.api import add_constant, OLS


def backward_elimination(x, y: Series, significance_level: float = 0.05) -> list:
    features = x.columns.values.tolist()
    while len(features) > 0:
        features_with_constant = add_constant(x[features], has_constant='add')
        model = OLS(y, features_with_constant).fit()
        p_values = Series(model.pvalues[1:], index=features)
        max_p_value = max(p_values)
        if max_p_value > significance_level:
            feature_with_p_max = p_values.idxmax()
            features.remove(feature_with_p_max)
        else:
            break

    return features
