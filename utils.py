import logging
import datetime as dt
import os


def create_logger(logger_name: str, log_filename: str):
    """
    log_filename: no suffix
    """
    dir_name = os.path.dirname(log_filename)
    if not os.path.isdir(dir_name):
        os.makedirs(dir_name)

    timestamp = dt.datetime.today().strftime("%Y%m%d%H%M%S")
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.DEBUG)
    handler = logging.FileHandler(f"{log_filename}_{timestamp}.log")
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter("%(asctime)s-%(levelname)s: %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger
