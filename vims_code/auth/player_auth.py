import datetime
import hashlib
import secrets
from _hashlib import HASH
from functools import lru_cache

from cachetools import lru

from vims_code.app import ApplicationException, ErrorCodes
from vims_code.auth.exceptions import PlayerAlreadyExists, WrongSession, PlayerNotFound, WrongPassword, SafetyFail

from vims_code.models.player_auth import PlayerAuth
from vims_code.models.player_game_2_team import PlayerGame2Team
from vims_code.models.player_list import PlayerList
from vims_code.models.team_game_auth import TeamGameAuth
from vims_code.models.team_player_role_list import TeamPlayerRoleList


class PlayerAuthClass(object):
    def __init__(self, conn):
        self.pl = PlayerList(conn)
        self.pa = PlayerAuth(conn)
        self.conn = conn

    async def identify_player_by_login(self, login: str) -> {}:
        try:
            res = (await self.pl.select(player_login=login))[0]
            return res
        except IndexError:
            return None

    async def identify_by_session(self, session_id):
        session_row = await self.pa.identify_by_session(session_id=session_id)
        if session_row is None:
            raise WrongSession('Сессия некорректна или истекла!')
        return session_row['player_id']

    async def register_player(self, login: str, pwd: str, email: str, player_type: str = 'HUMAN'):
        if await self.identify_player_by_login(login) is not None:
            raise PlayerAlreadyExists("Пользователь {login} уже существует".format(login=login))
        salt = str(secrets.token_hex(10))
        secret_hash: HASH = hashlib.sha256()
        secret_hash.update(pwd.encode())
        secret_hash.update(salt.encode())
        secret_hash_text: str = str(secret_hash.hexdigest())
        await self.pl.set(player_login=login,
                          player_pwd=secret_hash_text,
                          player_type=player_type,
                          email=email,
                          player_salt=salt)

    async def login(self, player_id: int) -> str:
        sid = str(secrets.token_hex(30))
        await self.pa.set(session_id=sid,
                          player_id=player_id,
                          date_start=datetime.datetime.now(),
                          num_of_devices=1)
        return sid

    async def auth(self, login: str, pwd: str) -> {}:
        player_row = await self.identify_player_by_login(login)
        if player_row is None:
            raise PlayerNotFound("Пользователь с логином {login} отсутствует в системе".format(login=login))

        secret_hash: HASH = hashlib.sha256()
        secret_hash.update(pwd.encode())
        secret_hash.update(player_row['player_salt'].encode())
        secret_hash_text = str(secret_hash.hexdigest())
        if player_row["player_pwd"] == secret_hash_text:
            sid = await self.login(player_row['id'])
        else:
            raise WrongPassword("Неверный пароль для пользователя с логином {login}".format(login=login))
        return {"sid": sid, "player_id": player_row['id'], "player_login": login}

    async def player_info(self, player_id):
        tprl = TeamPlayerRoleList(self.conn)
        player_team_roles = await tprl.select_player_team_info(player_id=player_id)
        pg2t = PlayerGame2Team(self.conn)
        player_games = await pg2t.select_player_games(player_id=player_id)
        return dict(player_team_roles=player_team_roles, player_games=player_games)

    async def accept_invitation(self, player_id, team_id, game_id, token):
        pg2t = PlayerGame2Team(self.conn)
        player_game_2_team_row = await pg2t.select(player_id=player_id, game_id=game_id)
        if len(player_game_2_team_row) > 0:
            if int(player_game_2_team_row[0]['team_id']) != team_id:
                raise SafetyFail("Вы уже играете в эту игру за другую команду!")
        await pg2t.set(player_id=player_id, team_id=team_id, game_id=game_id, token=token)

# self.set_user(user_login=login, user_name=user_name, pwd=secret_hash_text, salt=salt)
