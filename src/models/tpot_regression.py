from os import cpu_count

from tpot import TPOTRegressor

from .base_regression_model import BaseRegressionModel


class TPOTRegressionModel(BaseRegressionModel):
    def __init__(self):
        reg = TPOTRegressor()
        param_grid = {
            'verbosity': [3],
            'random_state': [55],
            'periodic_checkpoint_folder': ['intermediate_results'],
            'n_jobs': [cpu_count() // 2],
            'warm_start': [True],
            'generations': [20],
            'population_size': [80],
            'early_stop': [8]
        }
        super().__init__(reg, param_grid)
