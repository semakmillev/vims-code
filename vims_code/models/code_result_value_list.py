from sqlalchemy import text, or_
from vims_code.db.schema import t_code_result_value_list, t_code_list
from vims_code.models.api import DatabaseTable, Field, DbTypes
from vims_code.models.base import SqlTable


class CodeResultValueList(SqlTable):
    table = t_code_result_value_list

    async def multi_set(self, vals: []):
        return await super()._multi_set(vals, ['code_id', 'result_code'], True)

    async def set(self, id: int = None,
                  code_id: int = None,
                  result_code: str = None,
                  result_type: str = None,
                  result_value: str = None):

        res = await self.multi_set([{'id': id,
                                     'code_id': code_id,
                                     'result_code': result_code,
                                     'result_type': result_type,
                                     'result_value': result_value}])
        return res[0]

    async def get_code_result_values_by_level(self, level_id):
        sql = """select cpvl.*
                   from e_code.code_result_value_list cpvl
                  where code_id in (select id 
                                      from e_code.code_list cl where cl.level_id = :level_id)"""
        rows = (await self.conn.execute(text(sql), dict(level_id=level_id))).fetchall()
        code_dict = {}
        for row in rows:
            dict_id = f"{row['result_code']}|{row['result_type']}"
            try:
                code_dict[row['code_id']][dict_id] = row['result_value']
            except KeyError:
                code_dict[row['code_id']] = {dict_id: row['result_value']}
        return code_dict

    async def get_result_values_by_level(self, level_id):
        sql = """select cpvl.*
                   from e_code.code_result_value_list cpvl
                  where code_id in (select id from e_code.code_list cl where cl.level_id = :level_id)"""
        rows = (await self.conn.execute(text(sql), dict(level_id=level_id))).fetchall()
        return [dict(r) for r in rows]

    async def get_level_result_list(self, level_id):
        sql = """select distinct cpvl.result_code, cpvl.result_type
                   from e_code.code_result_value_list cpvl
                  where code_id in (select id 
                   from e_code.code_list cl where cl.level_id = :level_id)"""
        rows = (await self.conn.execute(text(sql), dict(level_id=level_id))).fetchall()
        return [dict(r) for r in rows]

    async def get_by_game(self, game_id):
        sql = """select * 
                   from e_code.code_result_value_list crvl,
                        e_code.code_list cl
                  where crvl.code_id = cl.id
                    and cl.level_id in (select id from e_code.level_list ll where ll.game_id = :game_id)
                  """
        rows = (await self.conn.execute(text(sql), dict(game_id=game_id))).fetchall()
        return [dict(r) for r in rows]

    async def select(self, code_id=None, level_id=None):
        sql = self.table.select().where(
            or_(self.table.c.code_id == code_id, code_id == None) &
            or_(self.table.c.code_id.in_(t_code_list.select().with_only_columns(t_code_list.c.id).where(
                t_code_list.c.level_id == level_id
            )), level_id == None)
        )
        rows = (await self.conn.execute(sql)).fetchall()
        return [dict(r) for r in rows]

    async def delete_by_code(self, code_id: int):
        sql = self.table.delete().where(self.table.c.code_id == code_id)
        await self.conn.execute(sql)
