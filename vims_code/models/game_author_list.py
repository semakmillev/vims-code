import datetime

from sqlalchemy import or_, text

from vims_code.db.schema import t_game_author_list
from vims_code.models.base import SqlTable


class GameAuthorList(SqlTable):
    table = t_game_author_list

    async def select(self, game_id, author_id):
        sql = self.table.select().where(
            or_(self.table.c.game_id == int(game_id), game_id == None)
            & or_(self.table.c.author_id == int(author_id), author_id == None)
        )

        rows = (await self.conn.execute(sql)).fetchall()
        return [dict(r) for r in rows]

    async def select_game_authors(self, game_id):
        sql = """select pl.id, pl.player_login, gal.author_role
                   from e_code.game_author_list gal,
                        e_code.player_list pl
                  where gal.author_id = pl.id
                    and game_id = %(game_id)s"""
        rows = (
            await self.conn.execute(
                text(sql),
                {"game_id": game_id},
            )
        ).fetchall()
        return [dict(r) for r in rows]

    async def select_author_games(self, author_id):
        sql = """select gl.id, gl.caption, gl.game_type, TO_CHAR(gl.creation_date,'DD.MM.YYYY') creation_date, gal.author_role
                           from e_code.game_author_list gal,
                                e_code.game_list gl
                          where gal.game_id = gl.id
                            and author_id = :author_id"""
        rows = (
            await self.conn.execute(
                text(sql),
                {"author_id": int(author_id)},
            )
        ).fetchall()
        return [dict(r) for r in rows]
