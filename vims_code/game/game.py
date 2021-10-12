import asyncio
import datetime
import os
from asyncio import sleep, Task

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine

from vims_code.app.funcs import sql_cache, game_load_cache, cache_tables
from vims_code.models.api import DatabaseConnectionPool, DatabaseConnection

# game_universe_object
from vims_code.models.game_list import GameList
from vims_code.models.game_team_info import GameTeamInfo
from vims_code.models.level_list import LevelList
from vims_code.models.team_level_list import TeamLevelList
from vims_code.models.tick_step import TickStep
from vims_code.game.levels import Level, LevelDict
from vims_code.game.team import Team


class GameTeamDict(dict):
    def __getitem__(self, item: int) -> Team:
        return super().__getitem__(item)

    def __setitem__(self, key, value: Team):
        return super().__setitem__(key, value)


class Game(object):
    def __init__(self, game_engine: AsyncEngine, game_id: int):
        self.game_engine: AsyncEngine = game_engine
        self.game_id = game_id
        self.game_connection = None
        self.gl: GameList = None  # GameList(self.game_connection)
        self.game_yaml = None
        # self.game_yaml = asyncio.get_event_loop().run_until_complete(self.get_game_yaml())
        self.level_inner_map = {}  # маппинг id на inner_id
        self.team_dict: GameTeamDict = GameTeamDict()
        self.level_dict: LevelDict = LevelDict()  # все уровни игры в словаре
        # self.set_cache()
        # self.load_levels()
        self.timer_task: Task = None
        # self.load_team    s()

    async def get_game_yaml(self):
        if not self.game_connection:
            self.game_connection = await self.game_engine.connect()

        return (await GameList(self.game_connection).get(id=self.game_id))["game_yaml"]

    async def set_cache(self, level_id=None, conn: AsyncConnection = None):
        need_2_close = False
        if not conn:
            conn = self.game_connection
        # conn = conn if conn else self.game_connection

        cache_rows = list(
            (
                await conn.execute(
                    text(sql_cache), dict(game_id=self.game_id, level_id=level_id)
                )
            ).fetchall()
        )

        table_cache = {}
        game_load_cache[self.game_id] = {}
        for table_index in range(0, len(cache_tables)):
            game_load_cache[self.game_id][cache_tables[table_index]] = cache_rows[
                table_index
            ]["table_json"]
            if not game_load_cache[self.game_id][cache_tables[table_index]]:
                game_load_cache[self.game_id][cache_tables[table_index]] = []
        print("cache loaded")

    def clear_cache(self):
        game_load_cache[self.game_id] = {}

    async def reload_level(self, level_id, conn: AsyncConnection):
        await self.set_cache(level_id, conn)
        level_rows = game_load_cache[self.game_id].get("level_list")

        updated_level = Level.init_level_from_row(conn, level_id, level_rows[0])
        # self.clear_cache()
        return updated_level

    async def load_levels(self):
        # game_load_cache[self.game_id]
        if not self.game_connection:
            self.game_connection = await self.game_engine.connect()

        ll = LevelList(self.game_connection)
        level_rows = (
            game_load_cache[self.game_id].get("level_list")
            if game_load_cache[self.game_id].get("level_list")
            else await ll.select(game_id=self.game_id)
        )
        print(f"Levels loading start...{datetime.datetime.now()}")
        for level_row in level_rows:
            self.level_inner_map[level_row["id"]] = level_row["inner_id"]
            level = Level(
                self.game_connection,
                level_row["id"],
                level_row["level_type"],
                level_row["caption"],
                level_row["inner_id"],
                level_row["condition_script"],
                level_row["failed_condition_script"],
                self.game_id)
            await level.load()
            self.level_dict[level_row["inner_id"]] = level

        print(f"Levels loading finish...{datetime.datetime.now()}")
        # self.clear_cache()

    async def load_teams(self, start_date):
        if not self.game_connection:
            self.game_connection = await self.game_engine.connect()

            # tll.set_levels_4_game(self.game_id)

        gti = GameTeamInfo(self.game_connection)
        game_team_info_rows = await gti.select(game_id=self.game_id, accepted=1)
        team_connection = self.game_connection  # _pool.acquire()
        for game_team_info_row in game_team_info_rows:
            team_id = game_team_info_row["team_id"]

            if team_id not in self.team_dict:
                level_script = self.game_yaml  # game_team_info_row['level_script']

                self.team_dict[team_id] = Team(
                    conn=team_connection,
                    team_id=team_id,
                    game=self,
                    level_script=level_script,
                    game_levels=self.level_dict,
                    game_levels_map=self.level_inner_map,
                )
                await self.team_dict[team_id].load_scores()
                self.team_dict[team_id].load_current_timer_values(start_date)
                self.team_dict[team_id].load_done_code_list()
                self.team_dict[team_id].conn = None
        # team_connection.conn.commit()
        # self.game_connection_pool.release(team_connection)

    async def prepare_game(
            self,
    ):
        # for team_id in self.team_dict:
        if not self.game_connection:
            self.game_connection = await self.game_engine.connect()
        ts = TickStep(self.game_connection)
        await TeamLevelList(self.game_connection).set_levels_4_game(self.game_id)
        await self.set_cache()
        await self.load_levels()
        await self.game_connection.commit()

    async def time_runner(self):
        steps = 0
        start_date_time = datetime.datetime.now()
        loop = asyncio.get_event_loop()
        while True:
            steps += 1
            for team in self.team_dict.values():
                team.step()
            # loop.create_task(self.step())
            # loop.create_task(self.inc_timers())
            # loop.create_task(self.tick_step.next_step(self.team_id, 1))

            await sleep(
                (
                        start_date_time
                        + datetime.timedelta(seconds=steps)
                        - datetime.datetime.now()
                ).microseconds
                / 1000000,
                loop=loop,
            )

    def start_game_timer(self):
        loop = asyncio.get_event_loop()
        self.timer_task = loop.create_task(self.time_runner())

    async def start_game(self):
        start_date = datetime.datetime.now()
        await self.prepare_game()
        await self.load_teams(start_date)
        async with self.game_engine.connect() as conn:
            for team_id in self.team_dict:
                team = self.team_dict[team_id]
                team.conn = conn
                await team.start_next_levels(start_date, False)
                team.conn = None
            self.start_game_timer()

    async def finish_game(self):

        if self.timer_task:
            self.timer_task.cancel()
        for team_id in self.team_dict:
            team = self.team_dict[team_id]
        await self.game_connection.close()

        # team.timer_task.cancel()

    @staticmethod
    async def clear(game_id, conn: AsyncConnection):
        if game_id in game_load_cache:
            del game_load_cache[game_id]
        sql = """delete from e_code.team_level_list tll 
                  where tll.level_id in (select id from e_code.level_list where game_id = :game_id)"""
        await conn.execute(text(sql), dict(game_id=game_id))
        sql = """delete from e_code.team_info_list til 
                  where til.info_id in (select id 
                                          from e_code.info_list il
                                         where il.level_id in (select id from e_code.level_list where game_id = :game_id))"""
        await conn.execute(text(sql), dict(game_id=game_id))
        sql = """delete from e_code.team_game_code_list
                   where code_id in (select id 
                                       from e_code.code_list cl
                                      where cl.level_id in (select id from e_code.level_list where game_id = :game_id))"""
        await conn.execute(text(sql), dict(game_id=game_id))
        sql = """delete from e_code.game_team_scores where game_id = :game_id"""
        await conn.execute(text(sql), dict(game_id=game_id))
        sql = """delete from e_code.tick_step ts
                  where ts.tick_id in (select id 
                                         from e_code.tick_list tl
                                        where tl.level_id in (select id from e_code.level_list where game_id = :game_id))"""
        await conn.execute(text(sql), dict(game_id=game_id))
        sql = """delete from e_code.team_info_list til where til.info_id in 
                    (select id 
                      from e_code.info_list il 
                     where il.level_id in (select id 
                                            from e_code.level_list ll where ll.game_id = :game_id))
        """
        await conn.execute(text(sql), dict(game_id=game_id))
        sql = """delete from e_code.team_timer_event_list ttel where tick_id in 
                            (select id 
                              from e_code.tick_list tl
                             where tl.level_id in (select id 
                                                     from e_code.level_list ll where ll.game_id = :game_id))
                """
        await conn.execute(text(sql), dict(game_id=game_id))

        await conn.commit()


class GameDict(dict):
    def __getitem__(self, item: int) -> Game:
        return super().__getitem__(item)

    def __setitem__(self, key, value: Game):
        return super().__setitem__(key, value)


games = GameDict()
