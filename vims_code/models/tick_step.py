from sqlalchemy import or_, text

from vims_code.db.schema import t_tick_step
from vims_code.models.base import SqlTable


class TickStep(SqlTable):
    table = t_tick_step

    async def select(self, id: int = None, team_id: int = None, tick_id: int = None):
        sql = self.table.select().where(
            or_(self.table.c.id == id, id == None)
            & or_(self.table.c.tick_id == tick_id, tick_id == None)
            & or_(self.table.c.team_id == team_id, team_id == None)
        )

        rows = (await self.conn.execute(sql)).fetchall()
        return [dict(r) for r in rows]

    async def select_level_steps(self, team_id, game_id):
        sql = """select ts.*, ll.id level_id, ll.inner_id level_inner_id
                   from e_code.tick_step ts,
                        e_code.tick_list tl,
                        e_code.level_list ll
                  where ts.tick_id = tl.id
                    and ll.id = tl.level_id
                    and ll.game_id = :game_id                                        
                    and ts.team_id = :team_id"""
        return await self.call_select(text(sql), dict(team_id=team_id, game_id=game_id))

    async def next_step(self, team_id: int, add_steps: int):
        try:
            sql = """update e_code.tick_step 
                        set num_of_steps = num_of_steps + %(add_steps)s
                      where team_id = %(team_id)s and tick_id in (select id 
                                                                    from e_code.tick_list tl 
                                                                   where tl.level_id in(select level_id
                                                                                          from e_code.team_level_list tll
                                                                                         where tll.team_id = %(team_id)s
                                                                                           and tll.level_status = 'PLAYING'))
                                                                                           """
            await self.conn.execute(text(sql), dict(team_id=team_id, add_steps=add_steps))
        except Exception as ex:
            print("!!!!", ex)

    async def create_game_ticks(self, game_id, team_id, start_date):
        sql = """            
        
            insert into e_code.tick_step (team_id, tick_id, num_of_steps)
             select %(team_id)s, tl.id, 0  
               from e_code.tick_list tl 
              where level_id in (select id 
                                   from e_code.level_list ll
                                  where ll.game_id = :game_id)
                and tl.id not in(select ts.tick_id from e_code.tick_step ts where ts.team_id = :team_id);
        """
        await self.conn.execute(text(sql), dict(team_id=team_id, game_id=game_id))

    async def delete_by_team(self, team_id: int):
        await self.conn.execute(self.table.delete().where(self.table.c.team_id == team_id))
