import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from config.paths_config import *
from imblearn.over_sampling import SMOTENC
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from utils.common_functions import load_data, read_yaml

from src.custom_exception import CustomException
from src.logger import get_logger

logger = get_logger(__name__)


class DataProcessor:
    def __init__(self):
        self.config = read_yaml(CONFIG_PATH)["data_processing"]
        self.raw_file_path = RAW_FILE_PATH
        self.processed_dir = PROCESSED_DIR
        self.processed_file_path = PREPROCESSED_DATA_FILE_PATH

        if not os.path.exists(self.processed_dir):
            os.makedirs(os.path.abspath(self.processed_dir), exist_ok=True)

    def preprocess_data(self) -> pd.DataFrame:
        """Preprocess the data by using different techniques"""
        try:
            logger.info("Initializing the Data Preprocessing...")
            logger.info(f"[1] Loading the  data from the path : {self.raw_file_path}")
            df = load_data(self.raw_file_path)

            logger.info(
                "[2] Dropping the column to be predicted from the training data..."
            )
            df.drop(columns=["Booking_ID"], axis=1, inplace=True)

            logger.info("[3] Dropping the duplicates...")
            df.drop_duplicates(inplace=True)

            logger.info(
                "[4] Extract Categorical and Numerical Columns from the YAML File..."
            )
            cat_columns = self.config["categorical_columns"]
            num_columns = self.config["numerical_columns"]

            logger.info("[5] Initializing Label Encoding...")

            label_encoder = LabelEncoder()

            mappings = {}

            for column in cat_columns:
                df[column] = label_encoder.fit_transform(df[column])

                mappings[column] = {
                    str(label): int(code)
                    for label, code in zip(
                        label_encoder.classes_,
                        label_encoder.transform(label_encoder.classes_),
                    )
                }

            with open("config/mapping.json", "w", encoding="utf-8") as file:
                json.dump(mappings, file, indent=4)

            logger.info(
                f"Mappings are stored at: {os.path.abspath(Path('config/mapping.json'))}"
            )

            logger.info("[6] Skewness Handling...")
            skew_threshold = self.config["skewness_threshold"]

            for col in num_columns:
                if df[col].skew() > skew_threshold:
                    logger.info(f"Skewness detected in columns: {col}")
                    df[col] = np.log1p(df[col])

            return df
        except Exception as e:
            logger.exception("Exception Occured while preprocessing data...")
            raise CustomException(e, sys) from None

    def balance_data(self, df) -> pd.DataFrame:
        """Handles the imbalanced dataset using the SMOTE (Synthetic Minority Oversampling Technique)."""
        try:
            logger.info("Handling Imbalanced features...")

            X = df.drop(columns=[TARGET_COLUMN], axis=1)
            Y = df[TARGET_COLUMN]

            smote = SMOTENC(
                categorical_features=[
                    col
                    for col in self.config["categorical_columns"]
                    if col != TARGET_COLUMN
                ],
                k_neighbors=5,
                random_state=42,
            )

            X_res, Y_res = smote.fit_resample(X, Y)

            balanced_df = pd.DataFrame(X_res, columns=X.columns)
            balanced_df["booking_status"] = Y_res
            logger.info("Data has been balanced successfully...")
            return balanced_df
        except Exception as e:
            logger.exception("Error while Balancing the data...")
            raise CustomException(e, sys) from None

    def feature_selection(self, df) -> pd.DataFrame:
        """Performs feature selection on the dataset and select the top 10 features with maximum importance."""

        try:
            X = df.drop(columns=[TARGET_COLUMN], axis=1)
            Y = df[TARGET_COLUMN]

            feature_model = RandomForestClassifier(random_state=42)

            feature_model.fit(X, Y)

            feature_importance = feature_model.feature_importances_

            feature_importance_df = pd.DataFrame(
                {"feature": X.columns, "importance": feature_importance}
            )

            sorted_feature_importance_df = feature_importance_df.sort_values(
                by="importance", ascending=False
            )

            top_features = list(
                sorted_feature_importance_df["feature"]
                .head(self.config["num_of_features"])
                .values
            )
            top_df = df[top_features + [TARGET_COLUMN]]

            return top_df
        except Exception as e:
            logger.exception("Error While Feature Selection.")
            raise CustomException(e, sys) from None

    def save_data(self, df) -> None:
        try:
            logger.info("Saving the data into the processed folder")

            df.to_csv(
                self.processed_file_path,
                index=False,
            )
            logger.info(
                f"Data Saved Successfully at: {os.path.abspath(self.processed_file_path)}"
            )
        except Exception as e:
            logger.exception(
                "Exception Occurred during conversion of DataFrame to CSV."
            )
            raise CustomException(e, sys)

    def run(self) -> None:
        preprocessed_data = self.preprocess_data()
        balanced_data = self.balance_data(preprocessed_data)
        feature_selected_df = self.feature_selection(balanced_data)

        self.save_data(feature_selected_df)


if __name__ == "__main__":
    data_preprocessing = DataProcessor()
    data_preprocessing.run()
