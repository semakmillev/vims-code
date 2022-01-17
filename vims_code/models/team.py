import datetime

from sqlalchemy import or_

from vims_code.db.schema import t_team, t_team_player_role_list
from vims_code.models.api import DatabaseTable, DbTypes, Field
from vims_code.models.base import SqlTable


class DatabaseTeam(SqlTable):
    table = t_team

    async def select(self, id: int = None, caption: str = None):
        sql = self.table.select().where(
            or_(self.table.c.id == id, id == None) &
            or_(self.table.c.caption == caption, caption == None)
        )

        rows = (await self.conn.execute(sql)).fetchall()
        return [dict(r) for r in rows]

    async def select_player_teams(self, player_id):
        t = t_team
        tprl = t_team_player_role_list
        sql = t.select().join(tprl, t.c.id == tprl.c.team_id).where(
            ((player_id == tprl.c.player_id) & (tprl.c.player_role == 'OWNER'))
        ).with_only_columns(t.c.id, t.c.caption, tprl.c.player_id)
        rows = (await self.conn.execute(sql)).fetchall()
        return [dict(r) for r in rows]
