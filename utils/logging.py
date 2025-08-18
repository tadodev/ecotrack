# utils/logging.py
import logging


def init_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('dashboard.log'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)
