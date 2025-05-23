from numbers import Number
from typing import Optional

from numpy import array, asarray, fill_diagonal, isnan, ma, nan
from pandas import DataFrame, factorize, get_dummies, isnull
from scipy import stats
from scipy.spatial.distance import cdist
from scipy.stats import hmean


def weighted_hamming(data: DataFrame):
    """Compute weighted hamming distance on categorical variables. For one variable, it is equal to 1 if
    the values between point A and point B are different, else it is equal to the relative frequency of the
    distribution of the value across the variable. For multiple variables, the harmonic mean is computed
    up to a constant factor.

    @params:
        - data = a pandas data frame of categorical variables

    @returns:
        - distance_matrix = a distance matrix with pairwise distance for all attributes
    """
    categories_dist = []

    for category in data:
        x = get_dummies(data[category])
        x_mean = x * x.mean()
        x_dot = x_mean.dot(x.transpose())
        x_np = asarray(x_dot.replace(0, 1, inplace=False))
        categories_dist.append(x_np)
    categories_dist = array(categories_dist)
    return hmean(categories_dist, axis=0)


def distance_matrix(
    data: DataFrame,
    numeric_distance: str = "euclidean",
    categorical_distance: str = "jaccard",
) -> Optional[DataFrame]:
    """Compute the pairwise distance attribute by attribute to account for different variables type:
    - Continuous
    - Categorical
    For ordinal values, provide a numerical representation taking the order into account.
    Categorical variables are transformed into a set of binary ones.
    If both continuous and categorical distance are provided, a Gower-like distance is computed and the numeric
    variables are all normalized in the process.
    If there are missing values, the mean is computed for numerical attributes and the mode for categorical ones.

    Note: If weighted-hamming distance is chosen, the computation time increases a lot since it is not coded in C
    like other distance metrics provided by scipy.

    @params:
        - data                  = pandas dataframe to compute distances on.
        - numeric_distances     = the metric to apply to continuous attributes.
                                  "euclidean" and "cityblock" are available.
                                  Default = "euclidean"
        - categorical_distances = the metric to apply to binary attributes.
                                  "jaccard", "hamming", "weighted-hamming" and "euclidean"
                                  available. Default = "jaccard"

    @returns:
        - the distance matrix
    """
    possible_continuous_distances = ["euclidean", "cityblock"]
    possible_binary_distances = ["euclidean", "jaccard", "hamming", "weighted-hamming"]
    number_of_variables = data.shape[1]
    number_of_observations = data.shape[0]

    # Get the type of each attribute (Numeric or categorical)
    is_numeric = [
        all(isinstance(n, Number) for n in data.iloc[:, i]) for i, x in enumerate(data)
    ]
    is_all_numeric = sum(is_numeric) == len(is_numeric)
    is_all_categorical = sum(is_numeric) == 0
    is_mixed_type = not is_all_categorical and not is_all_numeric

    if numeric_distance not in possible_continuous_distances:
        print(f"The continuous distance {numeric_distance} is not supported.")
        return None
    elif categorical_distance not in possible_binary_distances:
        print(f"The binary distance {categorical_distance} is not supported.")
        return None

    # Separate the data frame into categorical and numeric attributes and normalize numeric data
    number_of_numeric_var, number_of_categorical_var = 0, 0
    if is_mixed_type:
        number_of_numeric_var = sum(is_numeric)
        number_of_categorical_var = number_of_variables - number_of_numeric_var
        data_numeric = data.iloc[:, is_numeric]
        data_numeric = (data_numeric - data_numeric.mean()) / (
            data_numeric.max() - data_numeric.min()
        )
        data_categorical = data.iloc[:, [not x for x in is_numeric]]

        # Replace missing values with column mean for numeric values and mode for categorical ones. With the mode,
        # it triggers a warning: "SettingWithCopyWarning: A value is trying to be set on a copy of a slice from a
        # DataFrame" but the value are properly replaced
        data_numeric.fillna(data_numeric.mean(), inplace=True)
        for x in data_categorical:
            data_categorical[x].fillna(data_categorical[x].mode()[0], inplace=True)
    elif is_all_numeric:
        data.fillna(data.mean(), inplace=True)
    else:
        for x in data:
            data[x].fillna(data[x].mode()[0], inplace=True)

    # "Dummifies" categorical variables in place
    if not is_all_numeric and not (
        categorical_distance == "hamming" or categorical_distance == "weighted-hamming"
    ):
        if is_mixed_type:
            data_categorical = get_dummies(data_categorical)
        else:
            data = get_dummies(data)
    elif not is_all_numeric and categorical_distance == "hamming":
        if is_mixed_type:
            data_categorical = DataFrame(
                [factorize(data_categorical[x])[0] for x in data_categorical]
            ).transpose()
        else:
            data = DataFrame([factorize(data[x])[0] for x in data]).transpose()

    if is_all_numeric:
        result_matrix = cdist(data, data, metric=numeric_distance)
    elif is_all_categorical:
        if categorical_distance == "weighted-hamming":
            result_matrix = weighted_hamming(data)
        else:
            result_matrix = cdist(data, data, metric=categorical_distance)
    else:
        result_numeric = cdist(data_numeric, data_numeric, metric=numeric_distance)
        if categorical_distance == "weighted-hamming":
            result_categorical = weighted_hamming(data_categorical)
        else:
            result_categorical = cdist(
                data_categorical, data_categorical, metric=categorical_distance
            )
        result_matrix = array(
            [
                [
                    1.0
                    * (
                        result_numeric[i, j] * number_of_numeric_var
                        + result_categorical[i, j] * number_of_categorical_var
                    )
                    / number_of_variables
                    for j in range(number_of_observations)
                ]
                for i in range(number_of_observations)
            ]
        )

    fill_diagonal(result_matrix, nan)

    return DataFrame(result_matrix)


def knn_impute(
    target,
    attributes,
    k_neighbors: int,
    aggregation_method: str = "mean",
    numeric_distance: str = "euclidean",
    categorical_distance: str = "jaccard",
    missing_neighbors_threshold: float = 0.5,
) -> Optional[DataFrame]:
    """Replace the missing values within the target variable based on its k nearest neighbors identified with the
    attributes variables. If more than 50% of its neighbors are also missing values, the value is not modified and
    remains missing. If there is a problem in the parameters provided, returns None.
    If to many neighbors also have missing values, leave the missing value of interest unchanged.

    @params:
        - target                        = a vector of n values with missing values that you want to impute.
                                          The length has to be at least n = 3.
        - attributes                    = a data frame of attributes with n rows to match the target variable
        - k_neighbors                   = the number of neighbors to look at to impute the missing values. It has to
                                          be a value between 1 and n.
        - aggregation_method            = how to aggregate the values from the nearest neighbors
                                          (mean, median, mode)
                                          Default = "mean"
        - numeric_distances             = the metric to apply to continuous attributes.
                                          "euclidean" and "cityblock" available.
                                          Default = "euclidean"
        - categorical_distances         = the metric to apply to binary attributes.
                                          "jaccard", "hamming", "weighted-hamming" and "euclidean" available.
                                          Default = "jaccard"
        - missing_neighbors_threshold   = minimum of neighbors among the k ones that are not also missing inferring
                                          the correct value. Default = 0.5

    @returns:
        - target_completed              = the vector of target values with missing value replaced. If there is a
                                          problem in the parameters, return None
    """

    possible_aggregation_method = ["mean", "median", "mode"]
    number_observations = len(target)
    is_target_numeric = all(isinstance(n, Number) for n in target)

    if number_observations < 3:
        print("Not enough observations.")
        return None
    if attributes.shape[0] != number_observations:
        print(
            "The number of observations in the attributes variable is not matching the target variable length."
        )
        return None
    if k_neighbors > number_observations or k_neighbors < 1:
        print("The range of the number of neighbors is incorrect.")
        return None
    if aggregation_method not in possible_aggregation_method:
        print("The aggregation method is incorrect.")
        return None
    if not is_target_numeric and aggregation_method != "mode":
        print("The only method allowed for categorical target variable is the mode.")
        return None

    target = DataFrame(target)
    attributes = DataFrame(attributes)

    # Get the distance matrix and check whether no error was triggered when computing it
    distances = distance_matrix(attributes, numeric_distance, categorical_distance)
    if distances is None:
        return None

    # Get the closest points and compute the correct aggregation method
    for i, value in enumerate(target.iloc[:, 0]):
        if isnull(value):
            order = distances.iloc[i, :].values.argsort()[:k_neighbors]
            closest_to_target = target.iloc[order, :]
            missing_neighbors = [x for x in closest_to_target.isnull().iloc[:, 0]]
            # Compute the right aggregation method if at least more than 50% of the closest neighbors are not missing
            if sum(missing_neighbors) >= missing_neighbors_threshold * k_neighbors:
                continue
            elif aggregation_method == "mean":
                target.iloc[i] = ma.mean(
                    ma.masked_array(closest_to_target, isnan(closest_to_target))
                )
            elif aggregation_method == "median":
                target.iloc[i] = ma.median(
                    ma.masked_array(closest_to_target, isnan(closest_to_target))
                )
            else:
                target.iloc[i] = stats.mode(closest_to_target, nan_policy="omit")[0][0]

    return target
