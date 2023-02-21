import logging
from datetime import datetime
from os import path
import pathlib
from time import sleep

def add_log_info(logger, exchange) -> None:
    file = f'data/logs/{exchange}'
    time_stamp = datetime.now()  # - dt.timedelta(hours=6)
    time_stamp = time_stamp.strftime('%Y-%m-%d')
    if path.exists(file):
        file_handler = logging.FileHandler(f'{file}/{time_stamp}.log')
    else:
        pathlib.Path(file).mkdir(parents=True, exist_ok=True)
        sleep(0.5)
        file_handler = logging.FileHandler(f'{file}/{time_stamp}.log')
        
    # create a stream handler to log to the console
    stream_handler = logging.StreamHandler()
    # create a formatter for the log messages
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    # add the formatter to the handlers
    if not logger.handlers:
        file_handler.setFormatter(formatter)
        stream_handler.setFormatter(formatter)
        # add the handlers to the logger
        logger.addHandler(file_handler)
        logger.addHandler(stream_handler)