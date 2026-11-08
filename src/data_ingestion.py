import os
import sys

import pandas as pd
from config.paths_config import *
from google.cloud import storage
from sklearn.model_selection import train_test_split
from utils.common_functions import read_yaml

from src.custom_exception import CustomException
from src.logger import get_logger

logger = get_logger(__name__)


class DataIngestion:
    def __init__(self):
        self.config = read_yaml(CONFIG_PATH)["data_ingestion"]
        self.bucket_name = self.config["bucket_name"]
        self.bucket_file_name = self.config["bucket_file_name"]
        self.train_test_ratio = self.config["train_ratio"]

        os.makedirs(RAW_DIR, exist_ok=True)

        logger.info(
            f"Data Ingestion Started with '{self.bucket_name}' and file name: '{self.bucket_file_name}'"
        )

    def download_csv_from_gcp(self):
        try:
            client = storage.Client()
            bucket = client.bucket(self.bucket_name)
            blob = bucket.blob(self.bucket_file_name)

            if os.path.exists(RAW_FILE_PATH):
                logger.info("Deleting the exisitng CSV File...")
                os.remove(RAW_FILE_PATH)
                logger.info("Existing CSV File Successfully deleted.")

            logger.info("Initiating download of the data from GCP.")
            blob.download_to_filename(RAW_FILE_PATH)
            logger.info(f"Data has been successfully dowloaded at: {RAW_FILE_PATH}")
        except Exception as e:
            logger.exception("Error while downloading the data from GCP")
            raise CustomException(e, sys) from None

    def split_data(self):
        try:
            logger.info("Initiating Split Process...")

            data = pd.read_csv(RAW_FILE_PATH)
            train_df, test_df = train_test_split(data, train_size=self.train_test_ratio)

            logger.info("Saving the train and test files into CSV...")

            train_df.to_csv(
                TRAIN_FILE_PATH,
                index=False,
            )

            test_df.to_csv(TEST_FILE_PATH, index=False)

            logger.info(f"Train Data Saved to: {TRAIN_FILE_PATH}")
            logger.info(f"Test Data Saved to: {TEST_FILE_PATH}")
        except Exception as e:
            logger.exception("Error while splitting the data.")
            raise CustomException(e, sys) from None

    def run(self):
        try:
            logger.info("Starting the Data Ingestion...")
            self.download_csv_from_gcp()
            self.split_data()
            logger.info("Data Ingestion Completed Successfully.")

        except Exception as e:
            logger.exception("Error Occured in the Data Ingestion")
            raise CustomException(e, sys) from None

        finally:
            logger.info("Data Ingestion Completed")


if __name__ == "__main__":
    data_ingestion = DataIngestion()

    data_ingestion.run()
