import logging

logger = logging.getLogger("mddc")
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter(
    "%(asctime)s - %(levelname)s - "
    + "%(process)d:%(thread)d - "
    + "%(module)s: %(message)s"
)
ch.setFormatter(formatter)
logger.addHandler(ch)
