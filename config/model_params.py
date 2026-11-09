from scipy.stats import loguniform, randint, uniform

LIGHTGBM_PARAMS = {
    "n_estimators": randint(100, 501),
    "max_depth": randint(3, 13),
    "learning_rate": loguniform(0.01, 0.2),
    "num_leaves": randint(15, 64),
    "min_child_samples": randint(10, 61),
    "colsample_bytree": uniform(0.7, 0.3),
    "reg_lambda": uniform(0.0, 2.0),
}


RANDOM_SEARCH_PARAMS = {
    "n_iter": 30,
    "cv": 5,
    "n_jobs": 2,
    "verbose": 2,
    "random_state": 42,
    "scoring": "f1",
    "refit": True,
}
