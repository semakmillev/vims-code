from sqlalchemy import text

from vims_code.db.schema import t_code_param_value_list
from vims_code.models.api import DatabaseTable, Field, DbTypes
from vims_code.models.base import SqlTable


class CodeParamValueList(SqlTable):

    async def set(
            self, id: int, code_id: int, param_code: str, param_type: str, param_value: str
    ):
        return await super().set(
            id=id,
            code_id=code_id,
            param_code=param_code,
            param_type=param_type,
            param_value=param_value,
        )

    async def multi_set(self, vals: []):
        return await super()._multi_set(vals, ['code_id', 'param_code'], True)

    async def get_code_param_values_by_level(self, level_id):
        sql = """select cpvl.*
                           from e_code.code_param_value_list cpvl
                          where code_id in (select id from e_code.code_list cl where cl.level_id = :level_id)"""
        rows = (await self.conn.execute(text(sql), dict(level_id=level_id))).fetchall()
        code_dict = {}
        for row in rows:
            dict_id = f"{row['param_code']}|{row['param_code']}"
            try:
                code_dict[row["code_id"]][dict_id] = row["param_value"]
            except KeyError:
                code_dict[row["code_id"]] = {dict_id: row["param_value"]}
        return code_dict

    async def get_level_param_list(self, level_id):
        sql = """select distinct cpvl.param_code, cpvl.param_type
                   from e_code.code_param_value_list cpvl
                  where code_id in (select id from e_code.code_list cl where cl.level_id = :level_id)"""
        rows = (await self.conn.execute(text(sql), dict(level_id=level_id))).fetchall()
        return [dict(r) for r in rows]

    async def get_by_game(self, game_id):
        sql = """select * 
                   from e_code.code_param_value_list cpvl,
                        e_code.code_list cl
                  where cpvl.code_id = cl.id
                    and cl.level_id in (select id from e_code.level_list ll where ll.game_id = :game_id)
                  """

        rows = (await self.conn.execute(text(sql), dict(game_id=game_id))).fetchall()
        return [dict(r) for r in rows]

    async def delete_by_code(self, code_id):
        t_cpvl = t_code_param_value_list
        await self.conn.execute(t_cpvl.delete().where(t_cpvl.c.code_id == code_id))
