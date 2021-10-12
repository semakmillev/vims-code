import datetime

from sqlalchemy import or_

from vims_code.db.schema import t_team
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
