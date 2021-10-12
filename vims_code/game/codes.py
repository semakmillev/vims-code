from math import sin, cos, atan2, sqrt
from typing import List

from sqlalchemy.ext.asyncio import AsyncConnection

from vims_code.app.funcs import game_load_cache
from vims_code.models.code_result_value_list import CodeResultValueList
from vims_code.game.params import Result


class Code(object):
    code_inner_map = {}

    def __init__(self, conn: AsyncConnection, code_id, inner_id, code_type, caption, code_tags, level_id,
                 game_id):
        self.code_id = code_id
        self.code_type = code_type
        self.inner_id = inner_id
        if (inner_id):
            self.code_inner_map[inner_id] = code_id
        self.caption = caption
        self.code_tags = code_tags
        self.game_id = game_id
        self.conn = conn
        self.results: List[Result] = []

        self.level_id = level_id

    def __hash__(self):
        return f'C_{self.code_id}'




    async def load_results(self):
        crvl = CodeResultValueList(self.conn)
        code_cached_results = game_load_cache[self.game_id].get('code_result_value_list')

        result_rows = []  # cl.select_by_level(level_id=self.level_id)
        if code_cached_results:
            result_rows = list(filter(lambda el: el['code_id'] == self.code_id, code_cached_results))
        else:
            result_rows = await crvl.select(code_id=self.code_id)

        for result_row in result_rows:
            result_code = result_row["result_code"]
            result_type = result_row["result_type"]
            result_value = result_row["result_value"]
            self.results.append(Result(result_code, result_type, result_value))

    def json_info(self):
        res = {}
        res['type'] = self.code_type
        res['id'] = self.code_id
        res['caption'] = self.caption
        res['results'] = {}
        for result in self.results:
            res['results'][result.result_code] = result.json_info()
        return res


class CodeDict(dict):
    def __getitem__(self, item) -> Code:
        return super().__getitem__(item)

    def __setitem__(self, key, value: Code):
        super().__setitem__(key, value)
