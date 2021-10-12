from typing import List

from sqlalchemy.ext.asyncio import AsyncConnection

from vims_code.models.info_condition_list import InfoConditionList
from vims_code.models.info_list import InfoList
from vims_code.game.params import Condition, ConditionDict


class Info(object):

    @classmethod
    async def from_db(cls, conn: AsyncConnection, info_id):
        il = InfoList(conn)
        row = await il.get(id=info_id)
        return cls(conn, row['id'], row['info_caption'], row['info_text'], row['level_id'])

    def __init__(self, conn: AsyncConnection, info_id: int, inner_id, caption, info_text, condition_script,
                 level_id: int):
        self.info_id = info_id
        self.inner_id = inner_id
        self.caption = caption
        self.conn = conn
        self.level_id = level_id
        self.info_text = info_text
        self.condition_script = condition_script
        self.conditions: ConditionDict = ConditionDict()

    async def load(self):
        await self.load_conditions()
        # self.conditions: List[Condition] = []
        if self.condition_script is None or self.condition_script == '':
            cond_arr = []
            for c in self.conditions.values():
                if c.condition_type in ('>', '>=', '<=', '==', '<'):
                    cond_arr.append(
                        f"int(res.get_value(level_id, '{c.condition_code}')) {c.condition_type} int({c.condition_value})"
                    )
                if c.condition_type == '@':
                    cond_arr.append(f"code_inner_map.get('{c.condition_value}') in done_codes")
                    pass

            self.condition_script = " and ".join(cond_arr)
        # print(f'Condition script for level {self.level_id}: {self.condition_script}')
        self.condition_eval = None
        if self.condition_script != "" and self.condition_script is not None:
            self.condition_eval = compile(self.condition_script, '<condition_script>', 'eval')

    async def load_conditions(self):
        icl = InfoConditionList(self.conn)
        rows = await icl.select(info_id=self.info_id)
        for row in rows:
            self.conditions[row['condition_code']] = \
                Condition(row['condition_code'], row['condition_type'], row['condition_value'])

    def json_info(self, shown=True):
        res = {}
        res['id'] = self.info_id
        res['caption'] = self.caption
        res['info_text'] = self.info_text if shown else ''
        res['conditions'] = [c.json_info() for c in self.conditions.values()]
        return res

    '''
    def get_info_text(self):
        il = InfoList(self.conn)
        info_row = il.select(id=self.info_id)[0]
        return {'caption': info_row['caption'], 'info_text': info_row['info_text']}
    

    def get_and_check_simple_code(self, team_id: int, code_value: str, code_type: str = None) -> int:
        code_info = self.code_values.get(code_value)
        if code_info is None:
            raise CodeException(44, "Code not found")
        code_id = int(code_info['code_id'])
        tgcl = TeamGameCodeList(self.conn)
        team_code_rows = tgcl.select(code_id=code_id, team_id=team_id)
        if len(team_code_rows) > 0:
            raise CodeException(45, "Code already completed")
        return code_id

    def complete_code(self, code_id: int, team_id: int):
        """ No checks! """
        crl = CodeResultValueList(self.conn)
        cl = TeamGameCodeList(self.conn)
        gtr = GameTeamResults(self.conn)
        cl.set(id=None, team_id=team_id, code_id=code_id)
        for code_result_value_row in crl.select(code_id=code_id):
            result_code = str(code_result_value_row['result_code'])
            result_value = code_result_value_row['result_value']
            level_id = None if result_code.startswith("_") else self.level_id
            gtr.set(id=None,
                    game_id=self.game_id,
                    level_id=level_id,
                    result_code=result_code,
                    result_value=result_value,
                    source_code_id=code_id,
                    source_level_id=level_id,
                    team_id=team_id
                    )

    def get_level_status(self, team_id):
        tll = TeamLevelList(self.conn)
        return tll.select(level_id=self.level_id, team_id=team_id)[0]['level_status']
    '''


class InfoDict(dict):
    def __getitem__(self, item: str) -> Info:
        return super().__getitem__(item)

    def __setitem__(self, key, value: Info):
        super().__setitem__(key, value)
