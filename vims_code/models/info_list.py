from sqlalchemy import or_

from vims_code.db.schema import t_info_list
from vims_code.models.api import DatabaseTable, Field, DbTypes
from vims_code.models.base import SqlTable


class InfoList(SqlTable):
    table = t_info_list
    t_il = t_info_list

    async def select(self, id: int = None,
                     level_id: int = None,
                     inner_id: str = None, ):
        sql = self.table.select().where(
            or_(self.table.c.id == id, id == None) &
            or_(self.table.c.level_id == level_id, level_id == None) &
            or_(self.table.c.inner_id == inner_id, inner_id == None)
        ).order_by(
            self.table.c.inner_id, self.table.c.info_caption
        )

        rows = (await self.conn.execute(sql)).fetchall()
        return [dict(r) for r in rows]

    async def delete_by_level(self, level_id: int):
        await self.conn.execute(self.table.delete().where(self.table.c.level_id == level_id))
