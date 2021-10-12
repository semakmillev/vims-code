import datetime
from typing import List

from sqlalchemy.ext.asyncio import AsyncConnection

from vims_code.app import ApplicationException
from vims_code.app.funcs import game_load_cache
from vims_code.models.code_list import CodeList
from vims_code.models.code_value_list import CodeValueList
from vims_code.models.info_list import InfoList
from vims_code.models.level_condition_list import LevelConditionList
from vims_code.models.level_list import LevelList
from vims_code.models.level_result_value_list import LevelResultValueList
from vims_code.models.team_level_list import TeamLevelList
from vims_code.models.tick_list import TickList
from vims_code.game.codes import CodeDict, Code
from vims_code.game.infos import Info
from vims_code.game.params import Result, ConditionDict, Condition
from vims_code.ticks.api import Tick


class CodeException(ApplicationException):
    pass


class LevelFinishedException(ApplicationException):
    pass


class LevelBlockedException(ApplicationException):
    pass


class Level(object):
    @staticmethod
    def init_level_from_row(conn: AsyncConnection, level_id, level_row: {}):
        return Level(level_id=level_id,
                     conn=conn,
                     game_id=level_row['game_id'],
                     level_type=level_row['level_type'],
                     caption=level_row['caption'],
                     inner_id=level_row['inner_id'],
                     condition_script=level_row['condition_script'],
                     failed_condition_script=level_row['failed_condition_script'])

    @staticmethod
    async def init_level_from_db(conn: AsyncConnection, level_id: int):
        ll = LevelList(conn)
        level_row = (await ll.select(id=level_id))[0]
        return Level(level_id=level_id,
                     conn=conn,
                     game_id=level_row['game_id'],
                     level_type=level_row['level_type'],
                     caption=level_row['caption'],
                     inner_id=level_row['inner_id'],
                     condition_script=level_row['condition_script'],
                     failed_condition_script=level_row['failed_condition_script'])

    def __hash__(self):
        return f'L_{self.level_id}'

    def __init__(self, conn: AsyncConnection, level_id: int, level_type: str, caption: str,
                 inner_id: str,
                 condition_script: str,
                 failed_condition_script: str,
                 game_id: int,
                 db_info=None):
        self.level_id = level_id
        self.level_type = level_type
        self.caption = caption
        self.game_id = game_id
        self.inner_id = inner_id
        self.conn = conn
        self.code_values = {}
        self.level_loading_status = 'LOADED'
        self.location_code_values = {}
        self.codes: CodeDict = CodeDict()
        # self.load_code_list()
        self.ticks: List[Tick] = []
        self.failed_conditions: ConditionDict = ConditionDict()
        self.conditions: ConditionDict = ConditionDict()
        self.condition_script = condition_script
        self.failed_condition_script = failed_condition_script
        self.level_results: List[Result] = []
        self.failed_level_results: List[Result] = []
        self.info_list: List[Info] = []
        self.info_dict = {}
        self.condition_eval = None
        self.failed_condition_eval = None

    async def load(self):
        await self.load_results()
        await self.load_condition_values()
        await self.load_code_list()
        await self.load_code_values()
        await self.load_ticks()
        await self.load_infos()

        if (len(self.conditions.values()) == 0):
            raise ApplicationException(41, f'У уровня {self.inner_id} отсутствуют условия прохождения!')
        if self.condition_script is None or self.condition_script == '':
            # print(self.conditions.values())
            # cond_arr = [[c.condition_code, c.condition_type, c.condition_value] for c in self.conditions.values()]

            cond_arr = [
                f"int(res.get_value(level_id, '{c.condition_code}')) {c.condition_type} int({c.condition_value})"
                for c in self.conditions.values()]
            self.condition_script = " and ".join(cond_arr)
        # print(f'Condition script for level {self.level_id}: {self.condition_script}')

        if self.condition_script != "" and self.condition_script is not None:
            print(self.condition_script)
            self.condition_eval = compile(self.condition_script, '<condition_script>', 'eval')

        if (len(self.failed_conditions.values()) == 0):
            raise ApplicationException(41, f'У уровня {self.inner_id} отсутствуют условия слива!')
        failed_cond_arr = [
            f"int(res.get_value(level_id, '{c.condition_code}')) {c.condition_type} int({c.condition_value})"
            for c in self.failed_conditions.values()]
        self.failed_condition_script = " and ".join(failed_cond_arr)
        if self.failed_condition_script != "" and self.failed_condition_script is not None:
            self.failed_condition_eval = compile(self.failed_condition_script, '<failed_condition_script>', 'eval')

    def json_info(self):
        res = {}
        res['id'] = self.level_id
        res['caption'] = self.caption
        res['inner_id'] = self.inner_id
        res['condition_script'] = self.condition_script
        res['failed_condition_script'] = self.failed_condition_script
        res['condition'] = [c.json_info() for c in self.conditions.values()]
        res['type'] = self.level_type
        res['failed_condition'] = [c.json_info() for c in self.failed_conditions.values()]
        return res

    async def load_code_values(self):
        '''
        cvl = CodeValueList(self.conn)

        level_cached_results = game_load_cache[self.game_id].get('code_value_list')
        value_rows = []
        if level_cached_results:
            value_rows = list(filter(lambda el: el['level_id'] == self.level_id, level_cached_results))
        else:
            value_rows = cvl.select_by_level_and_types(level_id=self.level_id)

        for value_row in value_rows:
            try:
                self.code_values[value_row['code_value']].append(int(value_row['code_id']))
            except KeyError:
                self.code_values[value_row['code_value']] = [int(value_row['code_id'])]
        '''

    async def load_results(self):
        lrvl = LevelResultValueList(self.conn)
        level_cached_results = game_load_cache[self.game_id].get('level_result_value_list')
        level_result_rows = []
        if level_cached_results:
            for level_cache_result in level_cached_results:
                if level_cached_results['level_id'] == self.level_id:
                    level_result_rows.append(level_cache_result)
        else:
            level_result_rows = await lrvl.select(level_id=self.level_id)

        for level_result_row in level_result_rows:
            result_code = level_result_row["result_code"]
            result_type = level_result_row["result_type"]
            result_value = level_result_row["result_value"]
            if level_result_row["is_fail"] == 0:
                self.level_results.append(Result(result_code, result_type, result_value))
            else:
                self.failed_level_results.append(Result(result_code, result_type, result_value))

    async def load_condition_values(self):
        lcl = LevelConditionList(self.conn)

        level_condition_rows = []
        level_cached_results = game_load_cache[self.game_id].get('level_condition_list')

        if level_cached_results:
            level_condition_rows = list(
                filter(lambda el: str(el['level_id']) == str(self.level_id), level_cached_results))
        else:
            level_condition_rows = await lcl.select(level_id=self.level_id, is_fail=None)

        for level_condition_row in level_condition_rows:
            if level_condition_row['is_fail'] == 1:
                self.failed_conditions[level_condition_row['condition_code']] = \
                    Condition(
                        level_condition_row['condition_code'],
                        level_condition_row['condition_type'],
                        level_condition_row['condition_value'],
                        1)
            else:
                self.conditions[level_condition_row['condition_code']] = \
                    Condition(
                        level_condition_row['condition_code'],
                        level_condition_row['condition_type'],
                        level_condition_row['condition_value'],
                        0)

    async def load_infos(self):
        il = InfoList(self.conn)

        level_condition_rows = []
        level_cached_results = game_load_cache[self.game_id].get('info_list')
        rows = []
        if level_cached_results:
            rows = list(filter(lambda el: int(el['level_id']) == int(self.level_id), level_cached_results))
        else:
            rows = await il.select(level_id=self.level_id)

        for row in rows:
            i = Info(self.conn, row['id'],
                     row['inner_id'],
                     row['info_caption'],
                     row['info_text'],
                     row['condition_script'],
                     row['level_id'])
            await i.load()
            self.info_dict[row['id']] = i
            self.info_list.append(i)

    async def load_ticks(self):
        tl = TickList(self.conn)
        tick_rows = await tl.select(level_id=self.level_id)
        for tick_row in tick_rows:
            tick = Tick(self.conn, tick_row['id'],
                        tick_row['level_id'],
                        tick_row['tick_type'],
                        tick_row['step'],
                        tick_row['starts_from'],
                        tick_row['finish_at'])
            await tick.load_params()
            self.ticks.append(tick)
        pass

    async def load_code_list(self):
        cvl = CodeValueList(self.conn)
        rows = []
        '''
        level_cached_results = game_load_cache[self.game_id].get('code_value_list')
        rows = []
        if level_cached_results:
            rows = list(filter(lambda el: el['level_id'] == self.level_id, level_cached_results))
        else:
            rows = cvl.select_by_level_and_types(self.level_id)

        self.code_values = {row['code_value']: TypeValue(row['value_type'], row['code_id'])
                            for row in rows}
        '''
        cl = CodeList(self.conn)
        level_cached_results = game_load_cache[self.game_id].get('code_list')

        code_rows = []  # cl.select_by_level(level_id=self.level_id)
        if level_cached_results:
            code_rows = list(filter(lambda el: int(el['level_id']) == int(self.level_id), level_cached_results))
        else:
            code_rows = await cl.select_by_level(level_id=self.level_id)
        for code_row in code_rows:
            code_id = int(code_row['id'])
            code_values = code_row['code_values_info']
            for code_value in code_values.split('|'):
                if code_row['code_type'] == 'SIMPLE':
                    if self.code_values.get(code_value):
                        self.code_values[code_value].append(code_row['id'])
                    else:
                        self.code_values[code_value] = [code_row['id']]
                elif code_row['code_type'] == "LOCATION":
                    if self.location_code_values.get(code_value):
                        self.location_code_values[code_value].append(code_row['id'])
                    else:
                        self.location_code_values[code_value] = [code_row['id']]
            self.codes[code_id] = Code(self.conn, code_id, code_row['code_inner_id'], code_row['code_type'],
                                       code_row['caption'],
                                       code_tags=['code_tags'],
                                       level_id=self.level_id,
                                       game_id=self.game_id)
            await self.codes[code_id].load_results()

    def get_level_status(self, team_id):
        tll = TeamLevelList(self.conn)
        return tll.select(level_id=self.level_id, team_id=team_id)[0]['level_status']


class LevelDict(dict):
    def __getitem__(self, item: str) -> Level:
        return super().__getitem__(item)

    def __setitem__(self, key, value: Level):
        super().__setitem__(key, value)
