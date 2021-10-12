import asyncio
import datetime
import math
from asyncio import sleep
from asyncio.tasks import Task
from collections import namedtuple, deque
from concurrent.futures.thread import ThreadPoolExecutor
from functools import partial
from math import sin, cos, sqrt, atan2
from typing import List

import yaml
from sqlalchemy.ext.asyncio import AsyncConnection

from vims_code.app import logger
from vims_code.app.funcs import game_load_cache

from vims_code.models.game_team_scores import GameTeamScores
from vims_code.models.team_game_code_list import TeamGameCodeList
from vims_code.models.team_info_list import TeamInfoList
from vims_code.models.team_level_list import TeamLevelList
from vims_code.models.team_timer_event_list import TeamTimerEventList
from vims_code.models.tick_step import TickStep
from vims_code.game.codes import Code, CodeDict

from vims_code.game.levels import Level, LevelFinishedException, LevelDict, CodeException

from vims_code.game.params import Result, Condition
from vims_code.game.scores import Scores
from vims_code.game.team_timer import TeamTimer


def check_status_done(level_status):
    return 1 if level_status in ('FAILED', 'FINISHED') else 0


class TeamLevel(object):
    def __init__(self, level_id, team_id, parent_level_id, level_tree):
        self.level_id = level_id
        self.team_id = team_id
        self.parent_level_id = parent_level_id
        self.level_tree = level_tree


class TeamLevelTree(dict):
    def find(self, item) -> TeamLevel:
        res = self.get(item)
        if res:
            return res
        for tl in self.values():
            res = tl.level_tree.find(item)
            if res:
                return res
        return None

    def __getitem__(self, item) -> TeamLevel:
        return super().__getitem__(item)

    def __setitem__(self, key, value: TeamLevel):
        super().__setitem__(key, value)


class _Scores(dict):
    def __getitem__(self, item) -> Result:
        return super().__getitem__(item)

    def __setitem__(self, key, value: Result):
        super().__setitem__(key, value)


class TeamScores(object):
    def __init__(self):
        self.simple_level_scores = {}
        self.simple_game_scores = {}
        self.after_level_scores = {}
        self.after_game_scores = {}

    def get_simple_scores(self):
        res = {}
        res.update(self.simple_level_scores)
        res.update(self.simple_game_scores)
        return res

    def json_info(self):
        res = {}
        res['simple_game_scores'] = [self.simple_game_scores[score].json_info() for score in self.simple_game_scores]
        res['simple_level_scores'] = {}
        for level_inner_id in self.simple_level_scores:
            level_score: _Scores = self.simple_level_scores[level_inner_id]
            res['simple_level_scores'].update({level_inner_id:
                                                   {score: level_score[score].json_info() for score in level_score}
                                               })

        res['after_game_scores'] = [self.after_game_scores[score].json_info() for score in self.after_game_scores]
        res['after_level_scores'] = {}
        for level_inner_id in self.after_level_scores:
            level_score: _Scores = self.after_level_scores[level_inner_id]
            res['after_level_scores'].update({level_inner_id:
                                                  [level_score[score].json_info() for score in level_score]
                                              })
        return res

    def start_level(self, level_inner_id):
        print(f'{level_inner_id} started')
        self.simple_level_scores.update({level_inner_id: {'DURATION': 0}})
        self.after_level_scores.update({level_inner_id: {}})

    def add_score(self, level_inner_id, result: Result):
        if str(result.result_code).startswith("_"):
            self.add_game_score(result)
        else:
            self.add_level_score(level_inner_id, result)

    def init_level_score(self, level_inner_id: str, result: Result):
        if not level_inner_id in self.simple_level_scores:
            self.simple_level_scores[level_inner_id] = {}
            self.add_level_score(level_inner_id, result)

    def add_level_score(self, level_inner_id: str, result: Result):

        if result.result_type == 'SIMPLE':
            scores = self.simple_level_scores
        else:
            scores = self.after_level_scores
        if level_inner_id not in scores:
            scores[level_inner_id] = {}
        try:
            current_result: Result = scores[level_inner_id][result.result_code]
            current_result.add_result(result.result_value)
        except KeyError:
            scores[level_inner_id][result.result_code] = result

    def add_game_score(self, result: Result):
        if result.result_type == 'SIMPLE':
            scores = self.simple_game_scores
        else:
            scores = self.after_game_scores
        try:
            current_result: Result = scores[result.result_code]
            current_result.add_result(result.result_value)
        except KeyError:
            scores[result.result_code] = result

    def get_value(self, level_id, value_code: str):
        if value_code.startswith('_'):
            res = self.simple_game_scores.get(value_code)
            return res.result_value if res else 0
        else:
            res = self.simple_level_scores.get(level_id)
            if res:
                return res.get(value_code).result_value if res.get(value_code) else 0
            else:
                return 0


def get_team_level_tree(levels_yaml: {}, game_id, parent_level_id=None) -> TeamLevelTree:
    level_tree = TeamLevelTree()
    for level in levels_yaml['уровни']:
        child_level_tree = TeamLevelTree()
        if level.get('уровни'):
            child_level_tree = get_team_level_tree(level, game_id, level['id'])
        level_tree[level['id']] = TeamLevel(level['id'], game_id, parent_level_id, child_level_tree)
    return level_tree


class DictDeque(dict):
    def __getitem__(self, item) -> deque:
        return super().__getitem__(item)

    def __setitem__(self, key, value: deque):
        super().__setitem__(key, value)


class Team(object):
    def __init__(self, conn: AsyncConnection, team_id, game, game_levels: LevelDict, game_levels_map,
                 level_script=None):

        self.team_id = team_id
        self.game = game
        self.conn = conn
        self.game_levels_map = game_levels_map
        self.gts = GameTeamScores(conn)
        self.tgcl = TeamGameCodeList(conn)
        self.tick_step = TickStep(conn)
        self.tll = TeamLevelList(conn)
        self.til = TeamInfoList(conn)
        self.ttel = TeamTimerEventList(conn)
        self.team_level_list = list(filter(lambda el: el['team_id'] == self.team_id,
                                           game_load_cache[self.game.game_id]['team_level_list']))
        # self.tll.select_game_for_team(game_id=game_id, team_id=team_id)
        # self.level_done = {game_levels_map[team_level_row['level_id']]: team_level_row['done'] for team_level_row in
        #                   self.team_level_list}
        self.level_statuses = {}
        for team_level_row in filter(lambda l: self.team_id == l['team_id'],
                                     game_load_cache[self.game.game_id]['team_level_list']):
            self.level_statuses[team_level_row['level_id']] = team_level_row['level_status']
        self.level_script = yaml.safe_load(level_script)
        timer_rows = filter(lambda r: r['team_id'] == self.team_id,
                            game_load_cache[self.game.game_id]['team_timer_event_list'])
        self.current_timers = {}
        for timer_row in timer_rows:
            if timer_row['tick_id'] in self.current_timers:
                team_timer: TeamTimer = self.current_timers.get(timer_row['tick_id'])
            else:
                team_timer: TeamTimer = TeamTimer(timer_row['tick_id'], timer_row['level_id'])
                self.current_timers[timer_row['tick_id']] = team_timer
                # self.current_timers.get(timer_row['tick_id'])
            team_timer.add_event(timer_row['event'], timer_row['event_date'])
            if timer_row['event'] == 'FINISHED':
                del self.current_timers[team_timer.timer_id]

        self.level_tree: TeamLevelTree = get_team_level_tree(self.level_script,
                                                             self.game.game_id)  # дерево текущих уровней (идентификаторы)

        self.team_actions = []

        self.game_levels = game_levels

        self.done_codes: dict = {}
        self.received_codes: DictDeque = DictDeque()
        self.last_date_time = None
        self.start_date_time = None
        self.team_scores = None

    async def load_scores(self):
        self.team_scores = Scores(self.conn, self.team_id, self.game.game_id, self.game_levels)
        await self.team_scores.load_infos()

    def load_current_timer_values(self, start_date):
        for timer in self.current_timers.values():
            for i in range(timer.get_num_of_steps(start_date)):
                level = self.game_levels[self.game_levels_map[timer.level_id]]
                for tick in level.ticks:
                    self.team_scores.level_steps[level.inner_id] += 1
                    for tick_param in tick.params:
                        res = Result(tick_param.code, tick_param.type, tick_param.value)
                        self.team_scores.add_level_scores(level.inner_id,
                                                          res)

                # self.step()

    '''
    def init_scores(self):
        for level_id in self.game_levels_map.keys():
            self.team_scores.ad(level_id, Result('DURATION', 'SIMPLE', 0))
            self.team_scores.init_level_score(level_id, Result('POINTS', 'SIMPLE', 0))
    '''

    def get_current_levels(self, current_el=None):
        if current_el is None:
            current_el = self.level_script
        res = {}
        for e in current_el['уровни']:
            level_id = self.game_levels.get(e['id']).level_id
            if check_status_done(self.level_statuses.get(level_id)) == 0:
                child_levels = None
                if 'уровни' in e:
                    child_levels = self.get_current_levels(e)
                res.update({e['id']: child_levels})
                if e['порядок'] != 0:
                    break

        return res

    def get_current_level_dict(self):
        current_levels = self.get_current_levels()
        current_level_dict = {level_id: self.game_levels[level_id] for level_id
                              in self.current_levels_tree_to_row(current_levels)}
        return current_level_dict

    def load_done_code_list(self, level_inner_id=None):

        rows = filter(lambda el: el['team_id'] == self.team_id,
                      game_load_cache[self.game.game_id].get('team_game_code_list'))
        # self.tgcl.select_by_game(team_id=self.team_id, game_id=self.game_id)
        for row in rows:
            code_id = row['code_id']
            level_id = row['level_id']
            level_inner_id = self.game_levels_map[level_id]
            code = self.game_levels[level_inner_id].codes[code_id]
            self.done_codes[code_id] = {"code": code, "code_value": row['code_value']}
            self.set_code_results(level_inner_id, code)

    '''
    async def add_info_to_db(self, level_inner_id, info):
        current_loop = asyncio.get_event_loop()
        level = self.game_levels[level_inner_id]
        # self.til.set(id, team_id, info_id, info_status=)
        await current_loop.run_in_executor(self._executor,
                                           partial(self.til.set,
                                                   team_id=self.team_id,
                                                   info_id=info.info_id,
                                                   info_status='SHOWED'))
        self.conn.commit()
    
    
    def add_info_to_dict(self, level_inner_id, info, ignore_db=False):
        try:
            self.current_info_dict[level_inner_id][info.info_id] = info
        except KeyError:
            self.current_info_dict[level_inner_id] = InfoDict()
            self.current_info_dict[level_inner_id][info.info_id] = info
        if not ignore_db:
            loop = asyncio.get_event_loop()
            loop.create_task(self.add_info_to_db(level_inner_id, info))
    '''

    def refresh_level_infos(self, level: Level):
        for info in level.info_list:
            if info.info_id not in self.team_scores.infos.get(level.inner_id, {}):
                if info.condition_eval:
                    add_info = eval(info.condition_eval, dict(res=self.team_scores,
                                                              done_codes=self.done_codes,
                                                              code_inner_map=Code.code_inner_map,
                                                              level_id=level.inner_id))
                    # add_info = eval(info.condition_eval)

                    # for condition in info.conditions:
                    #    if not self._check_condition(condition, level.level_id):
                    #        add_info = False
                    #       break
                    if add_info:
                        self.team_scores.add_info_to_dict(level_inner_id=level.inner_id, info=info)
                else:
                    pass

        """ 
        def __get_current_scores_from_db(self, level_id):
            gtr = GameTeamResults(self.conn)
            team_scores :TeamScores = {}
            team_value_rows = gtr.select_current_values(self.game_id, self.team_id, level_id=level_id)
            for row in team_value_rows:
                result_type = row.get('result_type', None)
                result_code = row.get('result_code')
                result_value = row.get('result_value')
                if result_type is None or result_type in ('NUMBER', 'LEVEL_CHANGE_TIME', 'BONUS'):
                    team_value = team_scores.level_scores.get(result_code, {"val": 0, "type": result_type})
                    team_scores.update(dict(result_code=team_value['val'] + int(result_value), result_type=result_type))
                    # team_values.update({row['result_code']: dict()
                if result_type == 'CONCAT_TEXT':
                    team_value = team_scores.get(result_code, {"val": '', "type": "CONCAT_TEXT"})
                    team_scores.update(dict(result_code=team_value['val'] + str(result_value), result_type=result_type))
                if result_type == 'UNIQUE':
                    team_scores.update(dict(result_code=result_code, result_type=result_type))
    
            return team_scores
        """

    def finish_level(self, level: Level, success: bool):
        level_id = level.level_id
        inner_id = level.inner_id
        if check_status_done(self.level_statuses.get(level_id)) == 1:
            return
        if success:
            self.team_scores.add_level_result(level)
        else:
            '''TODO! Штрафы!!!'''
            pass
        loop = asyncio.get_event_loop()
        loop.create_task(self.tll.set_level_status(team_id=self.team_id,
                                                   level_id=level.level_id,
                                                   level_status='FINISHED' if success else 'FAILED',
                                                   dt=datetime.datetime.now(),
                                                   done=1))
        self.level_statuses[level_id] = 'FINISHED' if success else 'FAILED'
        '''
        self.tli.finish_level(team_id=self.team_id, level_id=level_id)
        self.gts.finish_level(level_id=level_id, game_id=self.game_id, team_id=self.team_id,
                              is_fail=0 if success else 1)
        '''

    def current_levels_tree_to_row(self, current_levels):
        res = []

        game = self.game
        for level in current_levels:
            if game.level_dict[level].level_type == 'AGGREGATE':
                res.extend(self.current_levels_tree_to_row(current_levels[level]))
                res.append(level)
            else:
                res.append(level)
        return res

    def check_level_finish(self, level: Level):
        parent_tree_level = self.level_tree.find(level.inner_id)
        current_level_tree: TeamLevelTree = self.level_tree.find(level.inner_id).level_tree
        all_children_done = len(current_level_tree.values()) > 0
        for tree_level in current_level_tree.values():
            if check_status_done(self.level_statuses[tree_level.level_id]) == 0:
                all_children_done = False
                break
        if all_children_done:
            # self.finish_level(parent_level, success = 1 == 1)
            raise LevelFinishedException(1, "Уровень пройден!")

        if parent_tree_level and parent_tree_level.parent_level_id:
            try:
                parent_level = self.get_current_level_dict()[parent_tree_level.parent_level_id]
            except KeyError:

                pass
            try:
                self.check_level_finish(parent_level)
            except LevelFinishedException as l_ex:
                self.finish_level(parent_level, success=l_ex.error == 1)
                raise LevelFinishedException(1, "Уровень пройден!")
        # print(level.condition_script)
        if level.condition_eval:
            if eval(level.condition_eval, {'res': self.team_scores, 'level_id': level.inner_id}):
                raise LevelFinishedException(1, "Уровень пройден!")
        if level.failed_condition_eval:
            if eval(level.failed_condition_eval, {'res': self.team_scores, 'level_id': level.inner_id}):
                raise LevelFinishedException(0, "Уровень провален!")
        # eval(level.condition_eval, {'res':self.team_scores}
        '''
        for condition in level.failed_conditions.values():
            if self._check_condition(condition,
                                     level.level_id):
                raise LevelFinishedException(0, "Уровень провален!")
        for condition in level.conditions.values():
            if not self._check_condition(condition,
                                         level.level_id):
                return False
        '''

    def set_levels_start(self, start_date: datetime.datetime):
        current_level_dict = self.get_current_level_dict()

        level_ids = [level.level_id for level in current_level_dict.values()]
        self.ttel.set_levels_start(self.team_id, level_ids, start_date)

        # self.start_date_time = datetime.datetime.now()
        # loop = asyncio.get_event_loop()
        # self.timer_task = loop.create_task(self.time_runner())

    async def start_next_levels(self, dt: datetime.datetime = datetime.datetime.now(), do_async=True):
        current_levels_dict = self.get_current_level_dict()
        try:
            for level_inner_id in current_levels_dict.keys():
                level_id = self.game_levels[level_inner_id].level_id
                if self.level_statuses[level_id] == 'PLANNED':
                    curr_loop = asyncio.get_event_loop()
                    if do_async:
                        curr_loop.create_task(
                            self.tll.set_level_status(self.team_id, level_id, 'STARTED', 0, dt))
                    else:
                        # curr_loop.run_until_complete(curr_loop.run_in_executor(self._executor,
                        await self.tll.set_level_status(self.team_id, level_id, 'STARTED', 0, dt)
                    self.level_statuses[level_id] = 'STARTED'
            return 1
        except Exception as ex:
            raise
            print('Wow', ex)
            return 0

    def step(self):
        # raise Exception("DEPRECATED!")
        # check_level_finish()
        for level_id, level in self.get_current_level_dict().items():
            try:
                self.check_level_finish(level)
                self.refresh_level_infos(level)
                self.team_scores.add_level_tick(level.inner_id)
            except LevelFinishedException as l_ex:
                # print(l_ex.message)
                self.finish_level(level, success=l_ex.error == 1)
                self.start_next_levels(datetime.datetime.now())
                # self.set_current_level_dict()

                # print(self.current_level_dict.items())
        # next_level???
        # next_level???

    '''
    async def inc_timers(self):
        curr_loop = asyncio.get_event_loop()
        await curr_loop.run_in_executor(self._executor, self.tick_step.next_step, self.team_id, 1)
        self.conn.commit()
        pass
    '''

    async def time_runner(self):
        raise Exception("deprecated")
        '''
        steps = 0
        start_date_time = datetime.datetime.now()
        loop = asyncio.get_event_loop()
        while True:
            steps += 1
            loop.create_task(self.step())
            loop.create_task(self.inc_timers())
            # loop.create_task(self.tick_step.next_step(self.team_id, 1))
            await sleep(
                (start_date_time + datetime.timedelta(seconds=1) - datetime.datetime.now()).microseconds / 1000000,
                loop=loop)
        '''

    def set_level_info_json(self, rows: {}):
        for k in rows:
            level = self.game_levels[k]
            if rows[k] is None:
                self.refresh_level_infos(level)
                rows[k] = level.json_info()
                rows[k]['infos'] = {}
                info_dict = rows[k]['infos']
                for info in level.info_list:
                    info_dict[info.info_id] = info.json_info(
                        info.info_id in self.team_scores.infos.get(level.inner_id, {}))
                rows[k]['done_codes'] = {}
                rows[k]['received_codes'] = list(self.received_codes.get(level.level_id, []))
                for code in level.codes.values():
                    rows[k]['done_codes'][code.code_id] = code.json_info()
                    if code.code_id in self.done_codes:
                        rows[k]['done_codes'][code.code_id]['done'] = 1
                        rows[k]['done_codes'][code.code_id]['code_value'] = \
                            self.done_codes[code.code_id]['code_value']
            else:
                # print(rows[k])
                buf = rows[k]
                rows[k] = {}
                rows[k] = level.json_info()
                rows[k]['levels'] = buf
                self.set_level_info_json(rows[level.inner_id]['levels'])

    def json_info(self):
        res = {}
        res['id'] = self.team_id
        res['levels'] = {}
        current_levels = self.get_current_levels()
        res['finished'] = 0
        if current_levels == {}:
            if sum([check_status_done(ls) for ls in self.level_statuses.values()]) == len(self.game_levels.values()):
                res['finished'] = 1
        res['levels'] = current_levels
        res['blocked_levels'] = {}
        for lev in self.team_scores.blocked_level_dict:
            # if self.team_scores.check_level_blocked(lev):
            res['blocked_levels'][lev] = self.team_scores.blocked_level_dict[lev]
        self.set_level_info_json(res['levels'])
        '''
        for level_id, level in self.current_level_dict.items():
            res['levels'][level.level_id] = level.json_info()
            res['levels'][level.level_id]['infos'] = {}
            info_dict = res['levels'][level.level_id]['infos']
            for info in level.info_list:
                info_dict[info.info_id] = info.json_info(info.info_id in self.current_info_dict)
            res['levels'][level.level_id]['done_codes'] = {}
            for code in level.codes.values():
                if code.code_id in self.done_codes:
                    res['levels'][level.level_id]['done_codes'][code.caption] = code.json_info()
        '''
        res['scores'] = self.team_scores.json_info()

        return res

    def get_and_check_simple_code(self, level_inner_id: str, code_value: str, code_type: str = None) -> List[Code]:
        current_level_dict = self.get_current_level_dict()
        level = current_level_dict[level_inner_id]
        code_ids = level.code_values.get(code_value)
        if code_ids is None:
            raise CodeException(44, "Code not found")
        codes: List[Code] = []
        for code_id in code_ids:
            if code_id in self.done_codes:
                pass
            else:
                # raise CodeException(45, "Code has already accepted")
                codes.append(level.codes[code_id])
        return codes

    @staticmethod
    def haversine(lat1, lon1, lat2, lon2):
        R = 6372800  # Earth radius in meters

        phi1, phi2 = math.radians(lat1), math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlambda = math.radians(lon2 - lon1)

        a = math.sin(dphi / 2) ** 2 + \
            math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2

        return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    def get_and_check_location_code(self, level_inner_id, user_location):  # lat_code, lon_code, lat, lon):
        lat, lon = user_location.split(',')
        lat, lon = float(lat), float(lon)
        PI = 3.14159
        earth_radius = 6371000
        logger.info(f'start {level_inner_id},  {user_location}, {datetime.datetime.now()}')
        level = self.get_current_level_dict()[level_inner_id]
        codes: List[Code] = []
        for code_location in level.location_code_values.keys():
            lat_code, lon_code = code_location.split(',')
            lat_code, lon_code = float(lat_code), float(lon_code)
            '''
            dlon = lon_code - lon
            dlat = lat_code - lat
            a = (sin(dlat / 2)) ** 2 + cos(lat) * cos(lat_code) * (sin(dlon / 2)) ** 2
            c = 2 * atan2(sqrt(a), sqrt(1 - a))
            distance = earth_radius * c
            '''
            distance = self.haversine(lat_code, lon_code, lat, lon)
            if distance < 50:
                code_ids = level.location_code_values.get(code_location)
                for code_id in code_ids:
                    if code_id in self.done_codes:
                        pass
                    else:
                        codes.append(level.codes[code_id])
        logger.info(f'finish {level_inner_id},  {user_location}, {datetime.datetime.now()}')
        if len(codes) == 0:
            raise CodeException(44, "Place not found")
        return codes

    async def set_db_code_done(self, code: Code, code_value):

        tick_step = self.team_scores.level_steps[self.game_levels_map[code.level_id]]
        await self.tgcl.set(
            team_id=self.team_id,
            code_id=code.code_id,
            insert_date=datetime.datetime.now(),
            code_value=code_value,
            tick_step=tick_step,
            level_id=code.level_id)

    async def set_levels_started(self):
        dt = datetime.datetime.now()
        for level_id, level in self.get_current_level_dict().items():
            await self.tll.set_level_status(team_id=self.team_id,
                                            level_id=level.level_id,
                                            level_status='STARTED',
                                            dt=dt,
                                            done=0)

    def set_code_results(self, level_inner_id, code):

        for code_result in code.results:
            if code_result.result_type == 'SIMPLE' and not code_result.result_code.startswith('_'):
                self.team_scores.add_level_scores(level_inner_id, code_result)
            if code_result.result_type == 'BLOCK':
                self.team_scores.block_level(level_inner_id, code_result.result_code, code_result.result_value)
            if code_result.result_code.startswith('_') or code_result.result_type in ('BONUS', 'PENALTY'):
                self.team_scores.game_results.append(code_result)
                self.team_scores.code_link_2_scores[code.code_id].append(f'G_{len(self.team_scores.game_results)}')
                self.team_scores.add_game_scores(code_result)
            if code_result.result_type == '@':
                if code_result.result_code == 'INFOS':
                    if not code_result.result_value or code_result.result_value == '':
                        continue
                    info_ids = code_result.result_value.split(',')
                    for global_info_id in info_ids:
                        level_inner_id = global_info_id.split(':')[0]
                        info_inner_id = global_info_id.split(':')[1]
                        for info in self.team_scores.level_dict[level_inner_id].info_list:
                            if info.inner_id == info_inner_id:
                                self.team_scores.add_info_to_dict(level_inner_id, info)
                '''
                if code_result.result_code == 'INFOS':
                    infos = code_result.result_value.split(',')
                    for info in self.game_levels[level_inner_id].info_list:
                        if info.inner_id in infos:
                            self.team_scores.add_info_to_dict(level_inner_id=level_inner_id, info=info)
                '''

    def do_code(self, level_inner_id: str, code_value: str, code_type: str = None):
        loop = asyncio.get_event_loop()
        try:
            self.received_codes[level_inner_id].appendleft(
                {"value": code_value, "send_date": datetime.datetime.now().strftime("%H:%M:%S")})
        except KeyError:
            self.received_codes[level_inner_id] = deque(maxlen=100)
            self.received_codes[level_inner_id].appendleft(
                {"value": code_value, "send_date": datetime.datetime.now().strftime("%H:%M:%S")})
        codes = []
        if code_type == 'SIMPLE' or code_type is None:
            codes: List[Code] = self.get_and_check_simple_code(level_inner_id, code_value, code_type)
        elif code_type == 'LOCATION':
            codes: List[Code] = self.get_and_check_location_code(level_inner_id, code_value)

        for code in codes:
            # self.set_code_results(level_inner_id, code)

            # self.team_scores.add_code_result(code, level_inner_id)
            self.set_code_results(level_inner_id, code)
            self.done_codes[code.code_id] = {"code": code, "code_value": code_value}
            loop.create_task(self.set_db_code_done(code, code_value))
        current_level_dict = self.get_current_level_dict()
        for curr_level in self.get_current_level_dict().values():
            self.refresh_level_infos(curr_level)
        try:
            res = self.check_level_finish(current_level_dict[level_inner_id])
        except LevelFinishedException:
            self.finish_level(current_level_dict[level_inner_id], True)
            current_levels = self.get_current_levels()

            # loop.create_task(self.set_levels_playing())
        return codes

        '''
        if code_info is None:
            raise CodeException(44, "Code not found")
        code_id = int(code_info['code_id'])

        team_code_rows = tgcl.select(code_id=code_id, team_id=team_id)
        if len(team_code_rows) > 0:
            raise CodeException(45, "Code already completed")
        return code_id
        '''

    """
        def do_tick(team: Team, tick: Tick):
            for tick_param in tick.params:
                team.team_scores.add_level_point(
                    tick.level_id,
                    Result(tick_param, tick.params[tick_param]['result_type'], tick.params[tick_param]['result_value'])
                )
            loop = asyncio.get_event_loop()
            ts = TickStep(team.conn)
            asyncio.create_task(
                loop.run_in_executor(t, ts.next_step(team.team_id, tick.tick_id, tick.step))
            )
    """

    """
    pass_sleep = False
    
    if check_level_finish(team, level):
        team.finish_level(level.level_id)
        team.get_current_levels()
        pass_sleep = True
    
    apply_infos_status(level_id)
    get_active_infos()
    add_tick_points
    
    do_tick(team, level.tick)
    if not pass_sleep:
        await sleep(1)
    """
