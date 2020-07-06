from .decision_tree_regression import DecisionTreeRegressionModel
from .dummy_regression import DummyRegressionModel
from .light_gbm_regression import LightGBMRegressionModel
from .linear_regression import LinearRegressionModel
from .mlp_regression import MLPRegressionModel
from .random_forest_regression import RandomForestRegressionModel
from .support_vector_regression import SupportVectorRegressionModel
from .tpot_regression import TPOTRegressionModel
from .xgboost_regression import XGBoostRegressionModel

__all__ = [
    'DecisionTreeRegressionModel',
    'DummyRegressionModel',
    'LightGBMRegressionModel',
    'LinearRegressionModel',
    'MLPRegressionModel',
    'RandomForestRegressionModel',
    'SupportVectorRegressionModel',
    'TPOTRegressionModel',
    'XGBoostRegressionModel'
]


def get_model_class(model):
    if model in __all__:
        return globals()[model]
    else:
        raise Exception(f'The agent name {model} does not exist')


def make_model(model):
    if model in __all__:
        return globals()[model]()
    else:
        raise Exception(f'The agent name {model} does not exist')
