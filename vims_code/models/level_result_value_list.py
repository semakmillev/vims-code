from sqlalchemy import or_, text

from vims_code.db.schema import t_level_result_value_list
from vims_code.models.api import DatabaseTable, Field, DbTypes
from vims_code.models.base import SqlTable


class LevelResultValueList(SqlTable):
    table = t_level_result_value_list

    async def select(
            self,
            id: int = None,
            level_id: int = None,
            result_type: int = None,
            result_code: str = None,
            is_fail: int = 0,
    ):
        sql = self.table.select().where(
            or_(self.table.c.id == id, id == None)
            & or_(self.table.c.level_id == level_id, level_id == None)
            & or_(self.table.c.result_type == result_type, result_type == None)
            & or_(self.table.c.result_code == result_code, result_code == None)
            & or_(self.table.c.is_fail == is_fail, is_fail == None)
        )

        rows = (await self.conn.execute(sql)).fetchall()
        return [dict(r) for r in rows]

    async def select_by_game(self, game_id):
        sql = """select * 
                   from e_code.level_result_value_list lrvl 
                  where lrvl.level_id in (select id from e_code.level_list where game_id = :game_id)"""
        return await self.call_select(text(sql), dict(game_id=game_id))

    async def delete_by_level(self, level_id: int):
        await self.conn.execute(self.table.delete().where(self.table.c.level_id == level_id))
