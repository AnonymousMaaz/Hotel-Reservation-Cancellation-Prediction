import logging
import os
from datetime import datetime

LOGS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "logs"))

os.makedirs(LOGS_DIR, exist_ok=True)
LOG_FILE = os.path.join(
    LOGS_DIR, f"log_{datetime.now().strftime('%d_%m_%Y_%H_%M_%S')}.log"
)

logging.basicConfig(
    filename=LOG_FILE,
    format=(
        "[%(asctime)s] "
        "[%(levelname)s] "
        "[%(name)s] "
        "[%(filename)s]:%(lineno)d "
        "- %(message)s"
    ),
    level=logging.INFO,
)


def get_logger(name):
    logger = logging.getLogger(name=name)
    logger.setLevel(logging.INFO)
    return logger
