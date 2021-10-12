from sqlalchemy import or_

from vims_code.db.schema import t_tick_list
from vims_code.models.api import DatabaseTable, Field, DbTypes
from vims_code.models.base import SqlTable


class TickList(SqlTable):
    table = t_tick_list

    async def select(self, id: int = None,
                     tick_type: str = None,
                     level_id: int = None):
        sql = self.table.select().where(
            or_(self.table.c.id == id, id == None)
            & or_(self.table.c.tick_type == tick_type, tick_type == None)
            & or_(self.table.c.level_id == level_id, level_id == None)
        )

        rows = (await self.conn.execute(sql)).fetchall()
        return [dict(r) for r in rows]
