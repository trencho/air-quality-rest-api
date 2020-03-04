import pandas as pd
import statsmodels.api as sm


def backward_elimination(X, y):
    features = list(X.columns)
    while len(features) > 0:
        features_with_constant = sm.add_constant(X[features], has_constant='add')
        model = sm.OLS(y, features_with_constant).fit()
        p = pd.Series(model.pvalues.values[1:], index=features)
        pmax = max(p)
        feature_with_p_max = p.idxmax()
        if pmax > 0.05:
            features.remove(feature_with_p_max)
        else:
            break
    selected_features = features

    return selected_features
