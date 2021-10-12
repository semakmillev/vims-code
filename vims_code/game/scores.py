import asyncio
import datetime
from concurrent.futures.thread import ThreadPoolExecutor
from functools import partial

from sqlalchemy.ext.asyncio import AsyncConnection

from vims_code.models.api import DatabaseConnection, DatabaseConnectionExecutor
from vims_code.models.team_info_list import TeamInfoList
from vims_code.game.levels import Level, LevelDict
from vims_code.game.infos import Info, InfoDict
from vims_code.game.codes import Code
# from vims_code.game.infos import

from vims_code.game.params import Result


class Scores(object):
    def __init__(self, conn: AsyncConnection, team_id, game_id, level_dict: LevelDict):
        self.results = []
        self.game_id = game_id
        self.team_id = team_id
        self.conn = conn
        self.til = TeamInfoList(self.conn)
        self.level_dict = level_dict
        self.code_link_2_scores = {}
        self.level_link_2_scores = {}
        self.blocked_level_dict = {}

        self.level_scores = {k: self.get_start_level_scores() for k in level_dict}
        self.game_scores = {}
        self.level_results = {k: [] for k in level_dict}
        self.level_steps = {k: 0 for k in level_dict}
        self.game_results = []
        self.infos = {k: InfoDict() for k in level_dict}

    def block_level(self, level_inner_id, blocking_code, blocking_steps: int):

        val = self.level_scores[level_inner_id].get(blocking_code, Result(blocking_code, 'SIMPLE', 0))
        self.blocked_level_dict[level_inner_id] = {'key': blocking_code,
                                                   'val': val.result_value + blocking_steps}

    def check_level_blocked(self, level_inner_id):
        blocking_steps = self.blocked_level_dict.get(level_inner_id)
        if blocking_steps:
            val = blocking_steps['val']
            key = blocking_steps['key']
            curr_score = self.level_scores[level_inner_id].get(key)
            curr_score = curr_score.result_value if curr_score else 0
            # print(curr_score, val)
            if val > curr_score:
                return True
            else:
                del self.blocked_level_dict[level_inner_id]
        return False

    def get_start_level_scores(self):
        return dict(DURATION=Result('DURATION', 'SIMPLE', 0),
                    POINTS=Result('POINTS', 'SIMPLE', 0))

    async def add_info_to_db(self, info):


        # self.til.set(id, team_id, info_id, info_status=)

        await self.til.set(
            team_id=self.team_id,
            info_id=info.info_id,
            info_status='SHOWED')
        await self.conn.commit()

    async def load_infos(self):
        for info_row in await self.til.select_game_for_team(team_id=self.team_id,
                                                            game_id=self.game_id):
            level_inner_id = info_row['inner_id']
            info_id = info_row['info_id']
            info: Info = self.level_dict[level_inner_id].info_dict[info_id]
            self.infos[level_inner_id][info_id] = info

    def add_info_to_dict(self, level_inner_id, info: Info):
        self.infos[level_inner_id][info.info_id] = info
        loop = asyncio.get_event_loop()
        loop.create_task(self.add_info_to_db(info))

    def add_game_scores(self, result: Result):
        if result.result_type == 'SIMPLE' or result.result_type == 'BONUS':
            try:
                self.game_scores[result.result_code].result_value += int(result.result_value)
            except KeyError:
                self.game_scores[result.result_code] = result
        elif result.result_type == 'PENALTY':
            try:
                self.game_scores[result.result_code].result_value -= int(result.result_value)
            except KeyError:
                self.game_scores[result.result_code] = result
                self.game_scores[result.result_code].result_value = -self.game_scores[result.result_code].result_value
        elif result.result_type == '@':
            if result.result_code in ('_INFOS', 'INFOS'):
                infos = result.result_value.split(',')
                for info_complex_id in infos:
                    level_inner_id, info_inner_id = info_complex_id.split(':')
                    for info in self.level_dict[level_inner_id].info_list:
                        if info.inner_id == info_inner_id:
                            self.add_info_to_dict(level_inner_id, info)

    def add_level_tick(self, level_inner_id, multiply=1, inc_step=True):
        level = self.level_dict[level_inner_id]
        for tick in level.ticks:
            self.level_steps[level.inner_id] += 1 * multiply if inc_step else 0
            for tick_param in tick.params:
                res = Result(tick_param.code, tick_param.type, int(tick_param.value) * multiply)
                self.add_level_scores(level.inner_id, res)
                self.check_level_blocked(level_inner_id)

    def add_level_scores(self, level_inner_id, result: Result):

        if result.result_type == 'SIMPLE':
            try:
                self.level_scores[level_inner_id][result.result_code].result_value += int(result.result_value)
            except KeyError:
                self.level_scores[level_inner_id][result.result_value] = result
        elif result.result_type == '@':
            if result.result_code == 'INFOS':
                infos = result.result_value.split(',')
                for info_inner_id in infos:
                    for info in self.level_dict[level_inner_id].info_list:
                        if info.inner_id == info_inner_id:
                            self.add_info_to_dict(level_inner_id, info)

    def add_code_result(self, code: Code, level_inner_id):
        raise Exception('deprecated!')
        pass
        self.code_link_2_scores[code.code_id] = []
        for result in code.results:
            if result.result_type == 'BLOCK':
                self.block_level(level_inner_id, result.result_code, result.result_value)
            if result.result_code.startswith('_') or result.result_type in ('BONUS', 'PENALTY'):
                self.game_results.append(result)
                self.code_link_2_scores[code.code_id].append(f'G_{len(self.game_results)}')
                self.add_game_scores(result)
            if result.result_type == 'SIMPLE':
                pass
            if result.result_code == 'INFOS':
                info_ids = result.result_value.split(',')
                for global_info_id in info_ids:
                    level_inner_id = global_info_id.split(':')[0]
                    info_inner_id = global_info_id.split(':')[1]
                    for info in self.level_dict[level_inner_id].info_list:
                        if info.inner_id == info_inner_id:
                            self.add_info_to_dict(level_inner_id, info)
                    # self.add_info_to_dict(level_inner_id, info_id)

            else:

                self.level_results[level_inner_id].append(result)
                self.code_link_2_scores[code.code_id].append(f'L_{len(self.level_results)}')

    def add_level_result(self, level: Level):
        self.level_link_2_scores[level.inner_id] = []
        for result in level.level_results:
            self.game_results.append(result)
            self.level_link_2_scores[level.inner_id].append(f'G_{len(self.game_results)}')
            self.add_game_scores(result)

    def change_code_result(self, code: Code, level_inner_id):
        code_result_dict = {f"{r.result_code}_{r.result_type}": r for r in code.results}
        rebuild_level = False
        rebuild_game = False
        # if code.code_id in self.code_link_2_scores:
        for code_scores in self.code_link_2_scores[code.code_id]:
            if str(code_scores).startswith('G_'):
                curr_res = self.game_results[int(code_scores[2:])]
                self.game_results[int(code_scores[2:])] = \
                    code_result_dict[f"{curr_res.result_code}_{curr_res.result_type}"]
                rebuild_game = True
            else:
                curr_res = self.level_results[level_inner_id][int(code_scores[2:])]
                self.level_results[level_inner_id][int(code_scores[2:])] = \
                    code_result_dict[f"{curr_res.result_code}_{curr_res.result_type}"]
                rebuild_level = True
        if rebuild_level:
            self.level_scores[level_inner_id] = {}
        if rebuild_game:
            self.rebuild_game_scores()

    def change_level_result(self, level: Level):
        level_result_dict = {f"{r.result_code}_{r.result_type}": r for r in level.level_results}
        rebuild_game = False
        for level_scores in self.level_link_2_scores:
            curr_res = self.game_results[int(level_scores[2:])]
            self.game_results[int(level_scores[2:])] = \
                level_result_dict[f"{curr_res.result_code}_{curr_res.result_type}"]
            rebuild_game = True
        if rebuild_game:
            self.rebuild_game_scores()

    def rebuild_level_scores(self, level_inner_id):

        self.level_scores[level_inner_id] = self.get_start_level_scores()
        for r in self.level_results[level_inner_id]:
            self.add_level_scores(level_inner_id, r)
        self.add_level_tick(level_inner_id, multiply=self.level_steps[level_inner_id], inc_step=False)

    def rebuild_game_scores(self):
        self.game_scores = {}
        for g in self.game_results:
            self.add_game_scores(g)

    def get_value(self, level_inner_id, result_code: str):
        if result_code.startswith('_'):
            res = self.game_scores.get(result_code)
            return res.result_value if res else 0
        else:
            res = self.level_scores[level_inner_id].get(result_code)
            return res.result_value if res else 0

    def json_info(self):
        res = {}
        res['game_scores'] = []
        res['bonus_scores'] = []
        for score in self.game_scores.values():
            if score.result_type == 'SIMPLE':
                res['game_scores'].append(self.game_scores[score.result_code].json_info())
            if score.result_type in ('BONUS', 'PENALTY'):
                res['bonus_scores'].append(self.game_scores[score.result_code].json_info())
        res['level_scores'] = {}
        for level_inner_id in self.level_scores:
            level_score = self.level_scores[level_inner_id]
            # print(level_inner_id, level_score)
            res['level_scores'].update({level_inner_id:
                                            {score: level_score[score].json_info() for score in level_score}
                                        })
        return res
