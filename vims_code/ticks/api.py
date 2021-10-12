from typing import List

from sqlalchemy.ext.asyncio import AsyncConnection

from vims_code.app.funcs import CodeTypeValueClass
from vims_code.models.tick_param_value_list import TickParamValueList


class Tick(object):
    def __init__(self, conn: AsyncConnection, tick_id: int = None, level_id=None, tick_type=None, step=None,
                 starts_from=None, finished_at=None):
        self.conn = conn
        self.tick_id = tick_id
        self.level_id = level_id
        self.tick_type = tick_type
        self.step = step
        self.starts_from = starts_from
        self.finished_at = finished_at
        self.params = List[CodeTypeValueClass]

    async def load_params(self):
        tpvl = TickParamValueList(self.conn)
        param_rows = await tpvl.select(tick_id=self.tick_id)

        self.params = [CodeTypeValueClass(row['param_code'],
                                          row['param_type'],
                                          row['param_value']) for row in param_rows]
        return self.params
