import os
import sys
from pathlib import Path

import pandas as pd
import yaml
from src.custom_exception import CustomException
from src.logger import get_logger

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
        logger.exception("Error reading the YAML File.")
        raise CustomException(e, sys) from None


def load_data(path: Path | os.PathLike):
    try:
        path = Path(path).expanduser().resolve()
        logger.info(f"Loading Data from path: {path}")
        return pd.read_csv(path)
    except Exception as e:
        logger.exception("Error while loading the data")
        raise CustomException(e, sys) from None


if __name__ == "__main__":
    contents = read_yaml("config/config.yaml")
    print(contents["data_processing"])
    # load_data("../artifacts/raw/train.csv")
