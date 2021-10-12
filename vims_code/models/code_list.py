from sqlalchemy import or_

from vims_code.db.schema import t_code_list
from vims_code.models.api import DatabaseTable, Field, DbTypes
from vims_code.models.base import SqlTable


class CodeList(SqlTable):
    table = t_code_list

    async def select_by_level(self, level_id: int, code_inner_id: str = None, code_type: str = None):
        t_cl = t_code_list
        sql = t_cl.select().where(or_(t_cl.c.code_type == code_type, code_type == None) &
                                  or_(t_cl.c.level_id == level_id, level_id == None) &
                                  or_(t_cl.c.code_inner_id == code_inner_id, code_inner_id == None))
        rows = (await self.conn.execute(sql)).fetchall()
        return [dict(r) for r in rows]

    async def select_by_game(self, game_id):
        sql = """select * 
                   from e_code.code_list cl 
                  where cl.level_id in (select id from e_code.level_list ll where ll.game_id = %(game_id)s)"""

        rows = (await self.conn.execute(sql, dict(game_id=game_id))).fetchall()
        return [dict(r) for r in rows]

    async def multi_set(self, code_arr, level_id) -> []:
        for el in code_arr:
            el['level_id'] = int(level_id)
        rows = await super()._multi_set(code_arr)

        for code_index in range(0, len(code_arr)):
            code_arr[code_index]['id'] = rows[code_index]['id']
        return code_arr

    def __multi_set(self, code_arr, level_id) -> []:
        raise Exception('123')
        for el in code_arr:
            el['level_id'] = level_id
        rows = super()._multi_set(code_arr)

        for code_index in range(0, len(code_arr)):
            code_arr[code_index]['id'] = rows[code_index]['id']
        return code_arr

    async def set(self, id: int = None,
                  caption: str = None,
                  code_type: str = None,
                  code_tags: str = None,
                  code_values_info: str = None,
                  code_inner_id: str = None,
                  level_id: int = None):
        return super().set(id=id,
                           caption=caption,
                           code_type=code_type,
                           code_tags=code_tags,
                           code_values_info=code_values_info,
                           code_inner_id=code_inner_id,
                           level_id=level_id)

    async def delete_by_inner_id(self, inner_id: str):
        await self.conn.execute(t_code_list.delete().where(t_code_list.c.code_inner_id == inner_id))
