import os
import sys
from os import PathLike
from pathlib import Path

import joblib as jb
import mlflow
import mlflow.sklearn
import pandas as pd
from config.model_params import *
from config.paths_config import *
from lightgbm import LGBMClassifier
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
from sklearn.model_selection import RandomizedSearchCV
from utils.common_functions import load_data

from src.custom_exception import CustomException
from src.logger import get_logger

logger = get_logger(__name__)


class ModelTrainer:
    def __init__(self):
        self.model_output_path = MODEL_OUTPUT_PATH
        self.train_file_path = PROCESSED_TRAIN_DATA_PATH
        self.test_file_path = PROCESSED_TEST_DATA_PATH

        self.lgbm_params = LIGHTGBM_PARAMS
        self.random_params_distribution = RANDOM_SEARCH_PARAMS

    def load_and_split_data(
        self,
    ) -> tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
        try:
            logger.info(
                f"Loading the data from the path: '{os.path.abspath(self.train_file_path)}' and '{self.test_file_path}'"
            )
            train_df = load_data(self.train_file_path)
            test_df = load_data(self.test_file_path)
            logger.info("Data Loaded Successfully!")

            logger.info("Splitting into train and test...")
            X_train = train_df.drop(columns=[TARGET_COLUMN], axis=1)
            Y_train = train_df[TARGET_COLUMN]

            X_test = test_df.drop(columns=[TARGET_COLUMN], axis=1)
            Y_test = test_df[TARGET_COLUMN]
            if X_train.columns.tolist() != X_test.columns.tolist():
                raise ValueError("Training and testing feature columns do not match!")
            logger.info(
                f"Dataset successfully splitted with shapes: [X_train: {X_train.shape}, X_test: {X_test.shape}, Y_train: {Y_train.shape}, Y_test: {Y_test.shape}]"
            )

            return X_train, X_test, Y_train, Y_test

        except Exception as e:
            logger.exception("Error while loading the data...")
            raise CustomException(e, sys) from e

    def train_model(self, X_train, Y_train) -> LGBMClassifier:
        """
        Trains and return the LGBM Classifier itself.

        Args:
            X_train: Independent Features to train the model.
            Y_train: Dependent Features to train the model.

        Return:
            LGBMClassifier: Trained Classifier Object.
        """
        try:
            logger.info("Initializing the Model.")
            lgbm_model = LGBMClassifier(
                boosting_type="gbdt",
                verbosity=-1,
                random_state=42,
                n_jobs=1,
            )

            logger.info("Starting with the HyperParameter Tuning...")

            random_search = RandomizedSearchCV(
                estimator=lgbm_model,
                param_distributions=self.lgbm_params,
                n_iter=self.random_params_distribution["n_iter"],
                cv=self.random_params_distribution["cv"],
                n_jobs=self.random_params_distribution["n_jobs"],
                verbose=self.random_params_distribution["verbose"],
                random_state=self.random_params_distribution["random_state"],
                scoring=self.random_params_distribution["scoring"],
                refit=self.random_params_distribution["refit"],
            )

            random_search.fit(X_train, Y_train)

            best_lgbm_params = random_search.best_params_
            best_model = random_search.best_estimator_

            logger.info(
                f"Best Params found with score: {random_search.best_score_} and params: {best_lgbm_params}"
            )

            return best_model
        except Exception as e:
            logger.exception(
                "Exception occured while Model Training and Hyperparameter Tuning..."
            )
            raise CustomException(e, sys) from e

    def evaluate_model(
        self, model: LGBMClassifier, X_test: pd.DataFrame, Y_test: pd.Series
    ) -> dict[str, float]:
        """Evaluates the trained classifier on the X_test and Y_test

        Args:
            X_test: Test DataFrame with TARGET_COLUMN dropped.
            Y_test: True answer of the independent features in X_test.

        Returns:
            dict[str, float]: Dictionary of metrics.
        """

        try:
            logger.info("Evaluating the model...")

            y_pred = model.predict(X_test)

            accuracy = accuracy_score(Y_test, y_pred)
            precision = precision_score(Y_test, y_pred)
            recall = recall_score(Y_test, y_pred)
            f1 = f1_score(Y_test, y_pred)

            logger.info(
                "Model Evaluation Metrics | "
                "Accuracy: %.4f | "
                "Precision: %.4f | "
                "Recall: %.4f | "
                "F1: %.4f",
                accuracy,
                precision,
                recall,
                f1,
            )

            return {
                "accuracy": accuracy,
                "precision": precision,
                "recall": recall,
                "f1": f1,
            }
        except Exception as e:
            logger.exception("Exception Occured while evaluating the model.")
            raise CustomException(e, sys) from None

    def save_model(self, model: LGBMClassifier, file_path: Path | PathLike) -> None:
        """Save the model into the provided file path.

        Args:
            model: The trained classifier to be saved.
            file_path: The path where the classifier is to be saved.
        """

        try:
            if not os.path.exists(file_path):
                os.makedirs(os.path.dirname(file_path), exist_ok=True)

            logger.info("Saving the model.")
            jb.dump(model, file_path)
            logger.info(f"Model saved successfully at:{os.path.abspath(file_path)}")
        except Exception as e:
            logger.exception("Exception occurred while saving the model")
            raise CustomException(e, sys) from e

    def run(self) -> None:
        try:
            PROJECT_ROOT = Path(__file__).resolve().parent.parent

            DB_PATH = PROJECT_ROOT / "mlflow.db"
            mlflow.set_tracking_uri(f"sqlite:///{DB_PATH.as_posix()}")

            mlflow.set_experiment("Hotel_Reservation")
            with mlflow.start_run():
                logger.info("MLFLOW Experimentation started...")
                logger.info("Model Training Pipeline Started...")
                logger.info("Logging the training and testing dataset to MLFLOW.")

                mlflow.log_artifact(self.train_file_path, artifact_path="datasets")
                mlflow.log_artifact(self.test_file_path, artifact_path="datasets")

                X_train, X_test, Y_train, Y_test = self.load_and_split_data()

                model = self.train_model(X_train=X_train, Y_train=Y_train)

                metrics: dict[str, float] = self.evaluate_model(
                    model=model, X_test=X_test, Y_test=Y_test
                )

                print(metrics)

                self.save_model(model=model, file_path=self.model_output_path)

                logger.info("Logging the model to the MLFLOW...")
                mlflow.log_artifact(self.model_output_path, artifact_path="models")

                logger.info("Logging params and metrics to MLFLOW...")
                mlflow.log_params(model.get_params())
                mlflow.log_metrics(metrics)

                logger.info("Model Training Pipeline completed successfully.")
        except Exception as e:
            logger.exception("Exception occurred in model training pipeline...")
            raise CustomException(e, sys) from None


if __name__ == "__main__":
    model_trainer = ModelTrainer()

    model_trainer.run()
