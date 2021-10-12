from vims_code.db.schema import t_code_value_list
from vims_code.models.api import DatabaseTable, Field, DbTypes
from vims_code.models.base import SqlTable


class CodeValueList(SqlTable):
    table = t_code_value_list

    async def set(
            self,
            id: int = None,
            code_id: int = None,
            value_type: str = None,
            code_value: str = None,
    ):
        return await super().set(
            id=id, code_id=code_id, value_type=value_type, code_value=code_value
        )

    async def select_by_level_and_types(
            self, level_id: int, code_type: str = None, value_type: str = None
    ):
        sql = """select cvl.*
                  from e_code.code_value_list cvl,
                       e_code.code_list cl
                 where cvl.code_id = cl.id                     
                   and (cl.code_type = :code_type or :code_typeis null)
                   and (cvl.value_type = :code_type or :code_typeis null)
                   and cl.level_id = :code_type"""
        rows = (await self.conn.execute(
            sql,
            {"level_id": level_id, "code_type": code_type, "value_type": value_type},
        )).fetchall()
        return [dict(r) for r in rows]

    async def select_by_game(self, game_id):
        sql = """select cvl.*
                   from e_code.code_value_list cvl,
                        e_code.code_list cl
                  where cvl.code_id = cl.id                                         
                    and cl.level_id = (select id from e_code.level_list where game_id = :game_od)"""
        rows = (await self.conn.execute(
            sql,
            {"game_id": game_id},
        )).fetchall()
        return [dict(r) for r in rows]

    async def delete_by_code(self, code_id: int):
        sql = self.table.delete().where(self.table.c.code_id == code_id)
        await self.conn.execute(sql)
