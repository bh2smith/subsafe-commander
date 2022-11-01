"""Easily set logger for each file that logs as

from src.log import set_log
log = set_log(__name__)
"""
import logging.config
from logging import Logger

from src.constants import LOG_CONFIG_FILE


def set_log(name: str) -> Logger:
    """Sets logger with `name` and provides project log config file"""
    log = logging.getLogger(name)

    logging.config.fileConfig(
        fname=LOG_CONFIG_FILE.absolute(), disable_existing_loggers=False
    )
    return log
