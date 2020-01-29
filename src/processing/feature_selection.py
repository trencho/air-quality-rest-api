import pandas as pd
import statsmodels.api as sm


def backward_elimination(X, y):
    cols = list(X.columns)
    while len(cols) > 0:
        X_1 = X[cols]
        X_1 = sm.add_constant(X_1, has_constant='add')
        model = sm.OLS(y, X_1).fit()
        p = pd.Series(model.pvalues.values[1:], index=cols)
        pmax = max(p)
        feature_with_p_max = p.idxmax()
        if pmax > 0.05:
            cols.remove(feature_with_p_max)
        else:
            break
    selected_features = cols

    return selected_features
