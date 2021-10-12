import json
import os
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
import logging
import sys


class ApplicationException(Exception):
    def __init__(self, error, message, status=500):
        self.error = error
        self.message = message
        self.status = status

    def json(self):
        return json.dumps({"error": self.code, "comments": self.reason})

    def __str__(self):
        return "%s: %s" % (self.code, self.reason)


class ErrorCodes:
    OBJECT_NOT_FOUND = 44
    APPLICATION_IS_EMPTY = 11
    AUTHORIZATION_FAILED = 43
    NOT_AUTHORIZED = 41
    ALREADY_EXISTS = 40
    TOTAL_FAIL = 50
    FORBIDDEN = 43
    OTHER = 99


log_levels = {"DEBUG": logging.DEBUG,
              "INFO": logging.INFO,
              "WARN": logging.WARN,
              "ERROR": logging.ERROR
              }

log_level = log_levels[os.environ['LOG_LEVEL'] if 'LOG_LEVEL' in os.environ else "DEBUG"]

pg_host = os.environ.get("PG_HOST")
print(pg_host)
engine: AsyncEngine = create_async_engine(pg_host, echo=False, pool_size=50)

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
