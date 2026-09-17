from numpy import column_stack, isfinite, ones
from numpy.linalg import matrix_rank
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


def estimable_features(x: DataFrame) -> list:
    """Columns whose coefficients OLS can actually identify, in the caller's order.

    A column that is an exact linear combination of the intercept and the columns before it
    has no unique coefficient, and elimination cannot remove it: statsmodels falls back to a
    pseudo-inverse, hands every collinear column ``p ~ 0``, and those columns are therefore
    never the argmax. The loop drops REAL features instead, to keep making progress.

    Two shapes of this were measured on the real training calls on 2026-09-17, and they are
    the same defect at different ranks:

    * **Constant columns.** A block of time features (``month_*``, ``quarter_*``, ``season_*``,
      ``days_in_month_*``, ``isLeapYear`` ...) never varies across a window shorter than the
      period it encodes. Fifteen such columns are mutually proportional and proportional to
      the intercept, collapsing that block to rank 1: the matrix was deficient by 14 in all 23
      calls, and elimination kept 12 of 12 and 14 of 14 of them.
    * **Nested indicators.** ``isYearStart`` implies ``isQuarterStart`` implies
      ``isMonthStart``. Over a window containing no month-start except 1 January the three are
      *identical* -- rank 1 of 3, found by taking the SVD of a real design matrix -- which was
      exactly the residual deficiency of 2 left after the constants were handled.

    The seed column is the intercept ``add_constant`` prepends later, so a constant column is
    just the rank-1 case of the same test rather than a rule of its own.

    Columns are scaled before the rank test. ``matrix_rank`` takes its tolerance from the
    largest singular value, and these features differ in scale by orders of magnitude
    (pollutant lags against cyclic encodings in [-1, 1]), so without scaling a small-magnitude
    column can be judged dependent purely for being small.

    Where columns alias, the FIRST in the frame's order is kept and the rest dropped. That is
    arbitrary but deterministic; nothing here can say which of an identical set is the
    meaningful one.
    """
    kept = []
    basis = ones((len(x), 1))
    for name in x.columns:
        column = x[name].to_numpy(dtype=float).reshape(-1, 1)
        if not isfinite(column).all():
            continue
        largest = abs(column).max()
        if largest == 0:
            continue
        candidate = column_stack([basis, column / largest])
        if matrix_rank(candidate) > basis.shape[1]:
            kept.append(name)
            basis = candidate
    return kept


def backward_elimination(
    x: DataFrame, y: Series, significance_level: float = 0.05
) -> list:
    features = estimable_features(x)
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
