from sqlalchemy import or_, text

from vims_code.db.schema import t_team_info_list
from vims_code.models.base import SqlTable


class TeamInfoList(SqlTable):
    table = t_team_info_list

    async def select(
            self,
            id: int = None,
            team_id: int = None,
            info_id: int = None,
            info_status: str = None,
            done: int = None,
    ):
        sql = self.table.select().where(
            or_(self.table.c.id == id, id == None)
            & or_(self.table.c.team_id == team_id, team_id == None)
            & or_(self.table.c.info_id == info_id, info_id == None)
            & or_(self.table.c.info_status == info_status, info_status == None)
            & or_(self.table.c.done == done, done == None)
        )

        rows = (await self.conn.execute(sql)).fetchall()
        return [dict(r) for r in rows]

    async def select_game_for_team(self, game_id: int, team_id: int, info_status: str = None):
        sql = """select info_id, ll.id level_id, ll.inner_id
                   from e_code.team_info_list til,
                        e_code.info_list il,
                        e_code.level_list ll
                where team_id = :team_id
                  and il.level_id = ll.id
                  and ll.game_id = :game_id
                  and il.id = til.info_id
                  and (cast(:info_status as varchar) is null or info_status = :info_status)
                """
        return await self.call_select(
            text(sql), {"game_id": game_id, "team_id": team_id, "info_status": info_status}
        )

    async def show_info(self, team_id: int, info_id: int):
        sql = """update e_code.team_level_list 
                    set level_status='SHOWED' 
                  where level_id = :level_id and team_id=:team_id"""
        await self.conn.execite(text(sql), dict(team_id=team_id, info_id=info_id))
