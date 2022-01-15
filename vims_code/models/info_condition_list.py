from sqlalchemy import or_, text

from vims_code.db.schema import t_info_condition_list, t_info_list
from vims_code.models.base import SqlTable


class InfoConditionList(SqlTable):
    table = t_info_condition_list

    async def select(
            self,
            id: int = None,
            info_id: int = None,
            level_id: int = None,
            condition_code: str = None,
    ):
        sql = self.table.select().where(
            or_(self.table.c.id == id, id == None)
            & or_(self.table.c.info_id == info_id, info_id == None)
            & or_(
                self.table.c.info_id.in_(
                    t_info_list.select().with_only_columns(t_info_list.c.id).where(t_info_list.c.level_id == level_id)
                ),
                level_id == None,
            )
            & or_(self.table.c.condition_code == condition_code, condition_code == None)
        )

        rows = (await self.conn.execute(sql)).fetchall()
        return [dict(r) for r in rows]

    async def set(
            self,
            id: int = None,
            info_id: int = None,
            condition_code: str = None,
            condition_type: str = None,
            condition_value: str = None,
    ):
        res = await self._multi_set(
            [
                {
                    "info_id": info_id,
                    "condition_code": condition_code,
                    "condition_type": condition_type,
                    "condition_value": str(condition_value),
                }
            ],
            ["info_id", "condition_code"],
            True,
        )
        return res[0]

    async def clear_by_code(self, code_inner_id, level_id):
        sql = """delete from e_code.info_condition_list
                  where condition_code = :code_inner_id
                    and info_id in (select id from e_code.info_list where level_id = :level_id)
                  """
        await self.conn.execute(
            text(sql), dict(code_inner_id=code_inner_id, level_id=level_id)
        )

    async def delete_by_info(self, info_id: int):
        sql = self.table.delete().where(self.table.c.info_id == info_id)
        await self.conn.execute(sql)
