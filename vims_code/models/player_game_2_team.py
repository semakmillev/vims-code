import datetime

from sqlalchemy import or_, text

from vims_code.db.schema import t_player_game_2_team
from vims_code.models.api import DatabaseTable, Field, DbTypes
from vims_code.models.base import SqlTable


class PlayerGame2Team(SqlTable):
    table = t_player_game_2_team

    async def select(self, id: int = None,
                     player_id: int = None,
                     token: str = None,
                     team_id: int = None,
                     game_id: int = None):
        sql = self.table.select().where(
            or_(self.table.c.id == id, id == None)
            & or_(self.table.c.player_id == player_id, player_id == None)
            & or_(self.table.c.token == token, token == None)
            & or_(self.table.c.team_id == team_id, team_id == None)
            & or_(self.table.c.game_id == game_id, game_id == None)
        )

        rows = (await self.conn.execute(sql)).fetchall()
        return [dict(r) for r in rows]

    async def select_player_games(self, player_id):
        sql = """select gl.id, gl.caption,gl.game_state, gl.game_type, pg2t.team_id
                   from e_code.game_list gl,
                        e_code.player_game_2_team pg2t
                  where gl.id = pg2t.game_id
                    and pg2t.player_id = :player_id
                """
        return await self.call_select(text(sql), dict(player_id=int(player_id)))
