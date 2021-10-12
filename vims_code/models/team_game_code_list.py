import datetime

from sqlalchemy import or_, text

from vims_code.db.schema import t_team_game_code_list
from vims_code.models.base import SqlTable


class TeamGameCodeList(SqlTable):
    table = t_team_game_code_list

    async def select(self, id: int = None,
                     team_id: int = None,
                     code_id: int = None,
                     level_id: int = None):
        sql = self.table.select().where(
            or_(self.table.c.id == id, id == None)
            & or_(self.table.c.team_id == team_id, team_id == None)
            & or_(self.table.c.code_id == code_id, code_id == None)
            & or_(self.table.c.level_id == level_id, level_id == None)

        )

        rows = (await self.conn.execute(sql)).fetchall()
        return [dict(r) for r in rows]

    async def select_by_game(self, team_id: int, game_id: int):
        sql = """select * from e_code.team_game_code_list t 
                  where t.level_id in (select id from e_code.level_list ll where game_id = :game_id)
                    and t.team_id = :team_id"""
        return await self.call_select(text(sql), dict(game_id=game_id, team_id=team_id))

    async def delete_by_team(self, team_id: int):
        await self.conn.execute(self.table.delete().where(self.table.c.team_id == team_id))
