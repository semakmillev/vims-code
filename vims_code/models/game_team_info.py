from sqlalchemy import or_, and_, text

from vims_code.db.schema import t_game_team_info
from vims_code.models.base import SqlTable


class GameTeamInfo(SqlTable):
    table = t_game_team_info

    async def select(self, game_id: int = None, team_id: int = None, accepted: int = 0):
        sql = self.table.select().where(
            or_(self.table.c.game_id == game_id, game_id is None)
            & or_(self.table.c.team_id == team_id, team_id is None)
            & or_(self.table.c.accepted == accepted, accepted is None)
        )
        rows = (await self.conn.execute(sql)).fetchall()
        return [dict(r) for r in rows]

    async def select_game_teams(self, game_id, accepted):
        sql = """select t.id, t.caption, gti.game_id
                   from e_code.game_team_info gti, 
                        e_code.team t 
                   where t.id = gti.team_id
                      and gti.accepted = :accepted
                     and gti.game_id = :game_id"""

        rows = (
            await self.conn.execute(text(sql), dict(game_id=game_id, accepted=accepted))
        ).fetchall()
        return [dict(r) for r in rows]

    async def set(
            self,
            id: int = None,
            game_id: int = None,
            team_id: int = None,
            level_script: int = None,
            accepted: int = 0,
    ):
        return await super().set(
            id=id,
            game_id=game_id,
            team_id=team_id,
            level_script=level_script,
            accepted=accepted,
        )

    async def get_player_team_registered(self, player_id, game_id):
        sql = """select t.*
                   from e_code.game_team_info gti,
                        e_code.team t 
                  where gti.team_id in(select r.team_id
                                     from e_code.team_player_role_list r where r.player_id = :player_id)
                    and game_id = :game_id
                    and t.id = gti.team_id"""

        rows = (
            await self.conn.execute(text(sql), dict(player_id=player_id, game_id=game_id))
        ).fetchall()
        return [dict(r) for r in rows]

    async def change_state(self, team_id, game_id, accepted):
        sql = self.table.update().values(
            accepted=accepted
        ).where(
            and_(self.table.c.game_id == game_id,
                 self.table.c.team_id == team_id)
        )
        await self.conn.execute(sql)

    async def set_level_script(self, game_id, level_script):
        sql = self.table.update().values(
            level_script=level_script
        ).where(
            and_(self.table.c.game_id == game_id,
                 self.table.c.level_script == None)
        )
        await self.conn.execute(sql)
