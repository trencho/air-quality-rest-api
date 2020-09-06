from pandas import Series
from statsmodels.api import add_constant, OLS


def backward_elimination(x, y):
    features = list(x.columns)
    while len(features) > 0:
        features_with_constant = add_constant(x[features], has_constant='add')
        model = OLS(y, features_with_constant).fit()
        p = Series(model.pvalues.values[1:], index=features)
        pmax = max(p)
        feature_with_p_max = p.idxmax()
        if pmax > 0.05:
            features.remove(feature_with_p_max)
        else:
            break
    selected_features = features

    return selected_features
