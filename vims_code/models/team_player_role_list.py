from sqlalchemy import or_, text

from vims_code.db.schema import t_team_player_role_list
from vims_code.models.base import SqlTable


class TeamPlayerRoleList(SqlTable):
    table = t_team_player_role_list

    async def select(self, id: int = None,
                     team_id: int = None,
                     player_id: int = None,
                     player_role: str = None):
        sql = self.table.select().where(
            or_(self.table.c.id == id, id == None)
            & or_(self.table.c.team_id == team_id, team_id == None)
            & or_(self.table.c.player_id == player_id, player_id == None)
            & or_(self.table.c.player_role == player_role, player_role == None)
        )

        rows = (await self.conn.execute(sql)).fetchall()
        return [dict(r) for r in rows]

    async def select_player_team_info(self, player_id):
        sql = """
            select tprl.player_role, t.id, t.caption
              from e_code.team_player_role_list tprl,
                   e_code.team t
             where t.id = tprl.team_id
               and player_id = :player_id
        """
        return await self.call_select(text(sql), dict(player_id=int(player_id)))
