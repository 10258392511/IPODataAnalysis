import fitz
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


def make_directories(filename: str):
    dir_name = os.path.dirname(filename)
    if not os.path.isdir(dir_name):
        os.makedirs(dir_name)


def combine_pdfs(out_filename: str, *filenames):
    doc_out = fitz.open()
    for filename in filenames:
        doc_iter = fitz.open(filename)
        doc_out.insert_pdf(doc_iter, 0, doc_iter.page_count)
        doc_iter.close()
    doc_out.save(out_filename)
