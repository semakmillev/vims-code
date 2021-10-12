from operator import or_

from sqlalchemy import text

from vims_code.db.schema import t_level_list
from vims_code.models.api import DatabaseTable, DbTypes, Field
from vims_code.models.base import SqlTable


class LevelList(SqlTable):
    table = t_level_list

    async def select(
            self,
            id: int = None,
            game_id: int = None,
            level_type: str = None,
            inner_id: str = None,
    ):
        sql = self.table.select().where(
            or_(self.table.c.id == id, id == None)
            & or_(self.table.c.game_id == game_id, game_id == None)
            & or_(self.table.c.level_type == level_type, level_type == None)
            & or_(self.table.c.inner_id == inner_id, inner_id == None)
        ).order_by(self.table.c.inner_id, self.table.c.id)

        rows = (await self.conn.execute(sql)).fetchall()
        return [dict(r) for r in rows]

    async def select_game_levels(self, game_id):
        sql = """select * 
                   from e_code.level_list ll 
                  where ll.game_id = :game_id and ll.level_type != 'DELETED'"""
        return await self.call_select(text(sql), dict(game_id=game_id))

    async def level_with_empty_inner_id(self, game_id):
        sql = """select * from e_code.level_list where game_id = :game_id and inner_id is null"""
        return await self.call_select(text(sql), dict(game_id=game_id))

    async def delete_by_game(self, game_id: int):
        await self.conn.execute(self.table.delete().where(self.table.c.game_id == game_id))
