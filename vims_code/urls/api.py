from sqlalchemy.ext.asyncio import AsyncConnection

from vims_code.auth.player_auth import PlayerAuthClass
from vims_code.models.team_game_auth import TeamGameAuth


class ActionRequest(object):
    action_list = {}

    def __init__(self, conn: AsyncConnection, player_id, game_id, team_id, game_token,
                 editing_game_id=None):
        self.conn = conn
        self.player_auth: PlayerAuthClass = PlayerAuthClass(self.conn)
        self.team_game_auth = TeamGameAuth(self.conn)
        self.player_id = player_id
        self.game_id = game_id
        self.team_id = team_id
        self.editing_game_id = editing_game_id
        self.game_token = game_token

    def convert_empty_2_none(self):
        try:
            for key in self.params:
                self.params[key] = None if self.params[key] == "" else self.params[key]
        except TypeError:
            if self.params is None:
                pass
            else:
                raise
