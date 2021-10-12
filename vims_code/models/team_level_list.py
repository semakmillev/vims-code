import datetime

# from vims_code.app import pool
from sqlalchemy import or_, text

from vims_code.db.schema import t_team_level_list, t_team_timer_event_list
from vims_code.models.api import DatabaseTable, Field, DbTypes
from vims_code.models.base import SqlTable


class TeamLevelList(SqlTable):
    table = t_team_level_list

    async def select(self, id: int = None,
                     team_id: int = None,
                     level_id: int = None,
                     level_status: str = None,
                     done: int = None):
        sql = self.table.select().where(
            or_(self.table.c.id == id, id == None) &
            or_(self.table.c.team_id == team_id, team_id == None) &
            or_(self.table.c.level_id == level_id, level_id == None) &
            or_(self.table.c.done == done, done == None) &
            or_(self.table.c.level_status == level_status, level_status == None)
        )
        return [dict(r) for r in (await self.conn.execute(sql)).fetchall()]

        # return super()._select(id=id, team_id=team_id, level_id=level_id, level_status=level_status, done=done)

    async def select_game_for_team(self,
                                   game_id: int,
                                   team_id: int,
                                   level_status: str = None,
                                   done: int = None):
        sql = """select * 
                   from e_code.team_level_list tli
                where team_id = :team_id
                  and tli.level_id in (select level_id from e_code.level_list where game_id = :game_id)
                  and (level_status = :level_status or :level_status is null)
                  and (done = :done or :done is null)
                """
        return await self.call_select(sql, {"game_id": game_id,
                                            "team_id": team_id,
                                            "level_status": level_status,
                                            "done": done})

    async def finish_level(self, team_id: int, level_id: int):
        sql = """update e_code.team_level_list 
                    set done = 1, 
                        level_status='DONE' 
                  where level_id = :level_id and team_id=:team_id"""
        await self.conn.execute(text(sql), dict(team_id=team_id, level_id=level_id))

    async def set_levels_4_team(self, team_id, game_id):
        sql = """
                insert into e_code.team_level_list(team_id, level_id, level_status, done)
                select %(team_id)s, id, 'PLANNED', 0 from e_code.level_list ll 
                 where game_id = %(game_id)s
                   and not exists(select * 
                                    from e_code.team_level_list tll 
                                   where tll.team_id = :team_id
                                     and tll.level_id = ll.id)
            """
        await self.conn.execute(text(sql), dict(team_id=team_id, game_id=game_id))

    async def set_levels_4_game(self, game_id):
        sql = """
            insert into e_code.team_level_list(team_id, level_id, level_status, done)
                select gti.team_id, ll.id, 'PLANNED', 0
                  From e_code.level_list ll,
                       e_code.game_team_info gti
                 where ll.game_id = :game_id
                   and ll.game_id = gti.game_id
                   and gti.accepted = 1
                   and not exists(select * 
                                    from e_code.team_level_list tll 
                                   where tll.team_id = gti.team_id
                                     and tll.level_id = ll.id)
        """
        await self.conn.execute(text(sql), dict(game_id=game_id))

    async def set_level_status(self, team_id: int, level_id: int, level_status: str, done: int, dt: datetime.datetime):
        sql = """update e_code.team_level_list 
                    set done = :done, 
                        level_status = :level_status
                  where team_id = :team_id and level_id = :level_id
                  """

        await self.conn.execute(text(sql), dict(team_id=team_id,
                                                level_id=level_id,
                                                done=done,
                                                level_status=level_status,
                                                dt=dt))
        sql = """insert into e_code.team_timer_event_list(team_id, tick_id, event, event_date) 
                    select :team_id, tl.id, :level_status, :dt
                      from e_code.tick_list  tl 
                     where level_id = :level_id"""
        await self.conn.execute(text(sql), dict(team_id=team_id,
                                                level_id=level_id,
                                                done=done,
                                                level_status=level_status,
                                                dt=dt))
        await self.conn.commit()


class TimerEvents:
    STARTED = 'STARTED'
    PAUSED = 'PAUSED'
    FINISHED = 'FINISHED'
    FAILED = 'FAILED'


class TeamTimerEventList(SqlTable):
    table = t_team_timer_event_list

    async def select(self, id: int = None,
                     # game_id: int = None,
                     team_id: int = None,
                     tick_id: int = None,
                     event: str = None):
        sql = self.table.select().where(
            or_(self.table.c.id == id, id == None) &
            or_(self.table.c.team_id == team_id, team_id == None) &
            or_(self.table.c.tick_id == tick_id, tick_id == None) &
            or_(self.table.c.event == event, event == None))

        return [dict(r) for r in (await self.conn.execute(sql)).fetchall()]

    async def set_levels_start(self, team_id, level_ids, dt: datetime.datetime):
        sql = """
            insert into e_code.team_timer_event_list(team_id, tick_id, event, event_date) 
            select %(team_id)s, tl.id, 'STARTED', %(event_date)s
              from e_code.tick_list  tl 
             where level_id in (select * from unnest(:level_ids))  
               and not exists(
                select * 
                  from e_code.team_timer_event_list ttel 
                 where ttel.team_id = :team_id
                   and ttel.tick_id = tl.id                             
               )           
        """
        await self.conn.execute(text(sql), dict(team_id=team_id, level_ids=level_ids, event_date=dt))

    # def set_level_event(self, team_id, level_id, event, event_date):
