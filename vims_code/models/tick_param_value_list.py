from sqlalchemy import or_

from vims_code.db.schema import t_tick_param_value_list
from vims_code.models.api import DatabaseTable, Field, DbTypes
from vims_code.models.base import SqlTable


class TickParamValueList(SqlTable):

    table = t_tick_param_value_list

    async def select(self, id: int = None,
                     tick_id: int = None,
                     param_code: str = None,
                     ):
        sql = self.table.select().where(
            or_(self.table.c.id == id, id == None)
            & or_(self.table.c.tick_id == tick_id, tick_id == None)
            & or_(self.table.c.param_code == param_code, param_code == None)
        )

        rows = (await self.conn.execute(sql)).fetchall()
        return [dict(r) for r in rows]
