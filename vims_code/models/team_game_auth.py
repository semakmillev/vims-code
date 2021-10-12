from sqlalchemy import or_, text

from vims_code.db.schema import t_team_game_auth
from vims_code.models.base import SqlTable


class TeamGameAuth(SqlTable):

    table = t_team_game_auth

    async def select(self, id: int = None,
                     team_id: int = None,
                     game_id: int = None,
                     token: str = None,
                     is_active: int = None):
        sql = self.table.select().where(
            or_(self.table.c.id == id, id == None)
            & or_(self.table.c.team_id == team_id, team_id == None)
            & or_(self.table.c.game_id == game_id, game_id == None)
            & or_(self.table.c.token == token, token == None)
            & or_(self.table.c.is_active == is_active, is_active == None)

        )

        rows = (await self.conn.execute(sql)).fetchall()
        return [dict(r) for r in rows]

    async def identify_by_session(self, token):
        return (await self.select(token=token, is_active=1))[0]

    async def deactivate_token(self, team_id, game_id):
        sql = """update e_code.team_game_auth tga
                    set  is_active = 0
                 where game_id = :game_id
                   and team_id = :team_id"""
        await self.conn.execute(text(sql), dict(team_id=team_id, game_id=game_id))
