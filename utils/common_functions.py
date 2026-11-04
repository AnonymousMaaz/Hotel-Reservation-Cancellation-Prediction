import yaml
import os
import pandas
import sys

from src.logger import get_logger
from src.custom_exception import CustomException

logger = get_logger(__name__)


def read_yaml(file_path: str):
    """Reads the YAML File and returns its content."""

    try:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File is missing at the given path: {file_path}")

        with open(file_path, "r") as yaml_file:
            config = yaml.safe_load(yaml_file)
            logger.info("Successfully read the YAML File contents.")

            return config
    except Exception as e:
        logger.error("Error reading the YAML File.")
        raise CustomException(e, sys) from None


# if __name__ == "__main__":
#     contents = read_yaml("config/config.yaml")
#     print(contents["data_ingestion"]["bucket_name"])
