from sqlalchemy import or_

from vims_code.db.schema import t_player_list
from vims_code.models.base import SqlTable


class PlayerList(SqlTable):
    table = t_player_list

    async def select(self, id: int = None,
               player_login: str = None,
               player_pwd: str = None,
               player_salt: str = None,
               player_type: str = None,
               player_state: str = None,
               email: str = None):
        sql = self.table.select().where(
            or_(self.table.c.id == id, id == None)
            & or_(self.table.c.player_login == player_login, player_login == None)
            & or_(self.table.c.player_state == player_state, player_state == None)
            & or_(self.table.c.player_type == player_type, player_type == None)
            & or_(self.table.c.email == email, email == None)
            & or_(self.table.c.player_pwd == player_pwd, player_pwd == None)
            & or_(self.table.c.player_salt == player_pwd, player_salt == None)

        )

        rows = (await self.conn.execute(sql)).fetchall()
        return [dict(r) for r in rows]
