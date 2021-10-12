import datetime
import secrets

from vims_code.app import ApplicationException
from vims_code.models.game_team_info import GameTeamInfo
from vims_code.models.team import DatabaseTeam
from vims_code.models.team_game_auth import TeamGameAuth
from vims_code.models.team_player_role_list import TeamPlayerRoleList


class TeamAuthClass(object):
    def __init__(self, conn):
        self.conn = conn
        self.tga = TeamGameAuth(conn)
        self.gti = GameTeamInfo(conn)

    async def generate_token(self, game_id, team_id) -> str:
        rows = await self.gti.select(game_id=game_id, team_id=team_id, accepted=1)
        if len(rows) == 0:
            raise ApplicationException(error=44, message="Team not registered to the game")
        await self.tga.deactivate_token(game_id=game_id, team_id=team_id)
        new_token = str(secrets.token_hex(25))
        await self.tga.set(team_id=team_id, game_id=game_id, token=new_token, is_active=1)
        return new_token

    async def get_game_token(self, game_id, team_id):
        try:
            return (await self.tga.select(team_id=team_id, game_id=game_id, is_active=1))[0]['token']
        except IndexError:
            return None
            # raise ApplicationException(error=44, message="Team not registered to the game")

    async def create_team(self, creator_id: int, caption: str):
        t = DatabaseTeam(self.conn)
        if len(await t.select(caption=caption)) > 0:
            raise ApplicationException(43, "Команда с таким названием уже существует!")
        team_id = await t.set(caption=caption, creation_date=datetime.datetime.now())
        tprl = TeamPlayerRoleList(self.conn)
        await tprl.set(player_id=creator_id, team_id=team_id, player_role='OWNER')
