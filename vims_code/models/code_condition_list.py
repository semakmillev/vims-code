raise Exception("frozen")
from sqlalchemy import text

from vims_code.db.schema import t_code_condition_list
from vims_code.models.base import SqlTable


class CodeConditionList(SqlTable):
    table = t_code_condition_list

    async def multi_set(self, vals: []):

        return await super()._multi_set(vals, ['code_id', 'condition_code'], True)

    async def set(self, id: int = None,
                  code_id: int = None,
                  condition_code: str = None,
                  condition_type: str = None,
                  condition_value: str = None):
        return await super().set(id=id, code_id=code_id,
                                 condition_code=condition_code,
                                 condition_type=condition_type,
                                 condition_value=condition_value)

    async def get_code_condition_list_by_level(self, level_id):
        sql = """select distinct cpvl.condition_code, cpvl.condition_type
                   from e_code.code_condition_list cpvl
                  where code_id in (select id from e_code.code_list cl where cl.level_id = :level_id)"""
        res = (await self.conn.execute(text(sql), parameters=dict(level_id=level_id))).fetchall()
        return [dict(r) for r in res]

    async def get_code_condition_values_by_level(self, level_id):
        sql = """select *
                   from e_code.code_condition_list ccl
                  where code_id in (select id from e_code.code_list cl where cl.level_id = :level_id)"""
        rows = (await self.conn.execute(text(sql), dict(level_id=level_id))).fetchall()
        code_dict = {}
        for row in rows:
            dict_id = f"{row['condition_code']}|{row['condition_type']}"
            try:
                code_dict[row['code_id']][dict_id] = row['condition_value']
            except KeyError:
                code_dict[row['code_id']] = {dict_id: row['condition_value']}
        return code_dict
        # return self.conn.call_select(sql, dict(level_id=level_id))

    async def get_by_game(self, game_id):
        sql = """select * 
                   from e_code.code_condition_list ccl,
                        e_code.code_list cl
                  where ccl.code_id = cl.id
                    and cl.level_id in (select id from e_code.level_list ll where ll.game_id = :game_id)
                  """
        return (await self.conn.execute(text(sql),
                                        dict(game_id=game_id))).fetchall()

    async def delete(self,
                     id: int):
        sql = t_code_condition_list.delete().where(t_code_condition_list.c.id == id)
        await self.conn.execute(sql)

    async def delete_by_code(self, code_id: int):
        sql = t_code_condition_list.delete().where(t_code_condition_list.c.code_id == code_id)
        await self.conn.execute(sql)
