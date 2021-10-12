import inspect
from enum import Enum

from psycopg2._psycopg import connection
from sqlalchemy.ext.asyncio import AsyncConnection

from vims_code.auth.exceptions import WrongSession
from vims_code.auth.player_auth import PlayerAuthClass
from call_api.consts import API_TYPE_DICT

from vims_code.models.api import DatabaseConnection
from collections import namedtuple

from vims_code.models.team_game_auth import TeamGameAuth

'''
from api import ErrorCodes
from api.exceptions import BusinessException
from api.role_owners import DbRoleOwnerClass, Application
from call_api.consts import API_TYPE_DICT
from db_api import DatabaseConnection
'''

api_connection: DatabaseConnection = None
api_token = None


class ActionInfo(object):
    __slots__ = ("func", "needs_auth", "needs_team_auth")

    def __init__(self, func, needs_auth, needs_team_auth):
        self.func = func
        self.needs_auth = needs_auth
        self.needs_team_auth = needs_team_auth


class SqlReqType(Enum):
    SELECT = 0
    PROCEDURE = 1
    FUNCTION = 2


def set_from_database_connection(db_conn: DatabaseConnection):
    global api_connection
    api_connection = db_conn


def set_api_token(token: str):
    global api_token
    api_token = token




