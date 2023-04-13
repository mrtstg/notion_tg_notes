import logging

_log_format = "%(asctime)s - [%(levelname)s]  - %(message)s"
log_formatter = logging.Formatter(_log_format)


def get_stream_handler(level: int = logging.ERROR) -> logging.StreamHandler:
    handler = logging.StreamHandler()
    handler.setLevel(level)
    handler.setFormatter(log_formatter)
    return handler


def get_logger(name: str, level: int = logging.ERROR) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(get_stream_handler(level))
    return logger
