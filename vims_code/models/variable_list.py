from sqlalchemy import text

from vims_code.db.schema import t_variable_list
from vims_code.models.base import SqlTable


class VariableList(SqlTable):
    table = t_variable_list

    async def select_game_vars(self, game_id):
        sql = 'select * from e_code.variable_list where game_id = :game_id or game_id is null'
        return await self.call_select(text(sql), dict(game_id=game_id))

    async def delete_by_game(self, game_id: int):
        await self.conn.execute(self.table.delete().where(self.table.c.game_id == game_id))
