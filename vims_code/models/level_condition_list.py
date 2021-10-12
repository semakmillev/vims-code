from sqlalchemy import or_, text

from vims_code.db.schema import t_level_condition_list
from vims_code.models.api import DatabaseTable, Field, DbTypes
from vims_code.models.base import SqlTable


class LevelConditionList(SqlTable):
    table = t_level_condition_list

    async def select(self, id: int = None,
                     level_id: int = None,
                     condition_code: str = None,
                     is_fail: int = 0):
        sql = self.table.select().where(
            or_(self.table.c.id == id, id == None) &
            or_(self.table.c.level_id == level_id, level_id == None) &
            or_(self.table.c.condition_code == condition_code, condition_code == None) &
            or_(self.table.c.is_fail == is_fail, is_fail == None)

        )
        rows = (await self.conn.execute(sql)).fetchall()
        return [dict(r) for r in rows]

    async def select_by_game(self, game_id):
        sql = """select * 
                   from e_code.level_condition_list lcl 
                  where lcl.level_id in (select id from e_code.level_list where game_id = :game_id)"""
        return await self.call_select(text(sql), dict(game_id=game_id))

    async def delete_by_level(self, level_id: int):
        await self.conn.execute(self.table.delete().where(self.table.c.level_id == level_id))

    async def clear_by_code(self, code_inner_id, level_id):
        sql = """delete from e_code.level_condition_list
                  where condition_code = :code_inner_id
                    and level_id = :level_id
                  """
        await (self.conn.execute(text(sql), {'code_inner_id': code_inner_id,
                                             'level_id': level_id}))
