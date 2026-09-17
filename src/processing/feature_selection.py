from pandas import DataFrame, Series
from statsmodels.api import OLS, add_constant


def get_p_values(x: DataFrame, y: Series, features: list) -> Series:
    # has_constant="skip", not "add". Forcing a second constant onto a frame that already
    # carries one makes the design matrix singular by construction, and a singular matrix is
    # what breaks the selection below: statsmodels falls back to a pseudo-inverse and hands
    # every mutually collinear column p ~ 0, which reads as perfectly significant.
    features_with_constant = add_constant(x[features], has_constant="skip")
    model = OLS(y, features_with_constant).fit()
    # Select by NAME. `pvalues[1:]` assumed an intercept that is always present and always
    # first, which only held while a constant was prepended unconditionally. Reindexing keeps
    # the caller's order and is correct whether or not one was added.
    return model.pvalues.reindex(features)


def backward_elimination(
    x: DataFrame, y: Series, significance_level: float = 0.05
) -> list:
    # Zero-variance columns are excluded before the loop, never by it.
    #
    # They are not a hypothetical. A block of time features (`month_*`, `quarter_*`,
    # `season_*`, `days_in_month_*`, `isLeapYear`, `isMonthEnd`, `isQuarter*`, `isYear*`) is
    # constant across any training window shorter than the period it encodes, and constant
    # columns are all proportional to one another and to the intercept. Measured 2026-09-17 on
    # a 12-to-17-day window: fifteen such columns collapsed that block to rank 1, leaving the
    # matrix rank-deficient by 14 in all 23 calls the suite makes.
    #
    # The loop cannot recover from that on its own. Collinear columns score p ~ 0, so they are
    # never the argmax and are never the ones removed -- it drops REAL features instead to keep
    # making progress. Both measured calls kept every constant they were given (12 of 12, then
    # 14 of 14) and eliminated 16 informative features to do it. The selection is then written
    # to selected_features.json and read back by the forecast path, where a column that was
    # constant during training is not constant any more.
    #
    # After this change the same two calls keep NO constant columns, and the design matrix is
    # rank-deficient by 2 rather than 14. Those two are exact dependencies among the VARYING
    # time features and are not addressed here; see
    # reports/feature-selection-rank-deficiency-2026-09-17.md.
    features = [name for name in x.columns if x[name].nunique(dropna=False) > 1]
    while len(features) > 0:
        p_values = get_p_values(x, y, features)
        # Pandas max/idxmax rather than the builtin: both skip NaN, which is what an
        # inestimable coefficient produces. Comparing a NaN with `>` is always False, so the
        # builtin would break the loop early and keep whatever it had.
        if p_values.max() > significance_level:
            features.remove(p_values.idxmax())
        else:
            break
    return features
