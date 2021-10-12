import datetime

from sqlalchemy import or_

from vims_code.db.schema import t_game_list
from vims_code.models.base import SqlTable


class GameList(SqlTable):
    table = t_game_list

    async def select(self, game_state=None):
        sql = self.table.select().where(
            or_(self.table.c.game_state == game_state, game_state == None)
        )
        return [dict(r) for r in (await self.conn.execute(sql)).fetchall()]
