from sqlalchemy.ext.asyncio import AsyncConnection

from vims_code.models.api import DatabaseConnection

# from vims_code.models.code_condition_list import CodeConditionList
from vims_code.models.code_list import CodeList
# from vims_code.models.code_param_value_list import CodeParamValueList
from vims_code.models.code_result_value_list import CodeResultValueList
# from vims_code.models.code_value_list import CodeValueList
from vims_code.models.info_condition_list import InfoConditionList
from vims_code.models.level_condition_list import LevelConditionList
from vims_code.models.level_list import LevelList


class CodeAdapter(object):
    def __init__(self, conn: AsyncConnection):
        self.conn = conn
        self.code_list = CodeList(conn)
        # self.code_value_list = CodeValueList(conn)
        self.code_result_value_list = CodeResultValueList(conn)
        # self.code_condition_list = CodeConditionList(conn)

    async def get_code_by_inner_id(self, inner_id: str, level_id: int):
        try:
            return (await self.code_list.select_by_level(code_inner_id=inner_id, level_id=level_id))[0]
        except IndexError:
            return None

    # async def clear_code_links(self, code_inner_id, level_id):
    #    await InfoConditionList(self.conn).clear_by_code(code_inner_id, level_id)

    async def delete_code(self, code_id):
        # await self.code_param_value_list.delete_by_code(code_id)
        await self.code_result_value_list.delete_by_code(code_id)
        # await self.code_value_list.delete_by_code(code_id)
        # await self.code_condition_list.delete_by_code(code_id)
        await self.code_list.delete(code_id)

    async def set_by_request_code(self,
                                  code_inner_id: str,
                                  info_inner_id: str,
                                  penalty: int,
                                  level_id: int):
        code = await self.get_code_by_inner_id(code_inner_id, level_id)
        level_inner_id = (await LevelList(self.conn).get(id=level_id))['inner_id']
        full_info_id = f"{level_inner_id}:{info_inner_id}"
        if code is None:
            code_id = await self.code_list.set(code_type="SIMPLE",
                                               caption=code_inner_id,
                                               code_values_info=code_inner_id,
                                               code_inner_id=code_inner_id)
            '''
            await self.code_value_list.set(code_id=code_id,
                                           value_type='TEXT',
                                           code_value=code_inner_id)
            '''
            await self.code_result_value_list.set(code_id=code_id,
                                                  result_code='SHOW_INFOS',
                                                  result_type='LIST',
                                                  result_value=full_info_id)

        else:
            code_id = int(code['id'])
            current_info_result = await self.code_result_value_list.set(code_id=code_id,
                                                                        result_code='SHOW_INFOS')
            if len(current_info_result) > 0:
                info_ids: [] = current_info_result['result_value'].split(',')
                if not full_info_id in info_ids:
                    info_ids.append(full_info_id)
                    await self.code_result_value_list.set(
                        code_id=code_id,
                        result_code='SHOW_INFOS',
                        result_type='LIST',
                        result_value=','.join(info_ids))

        await self.code_result_value_list.set(code_id=code_id,
                                              result_code='PENALTY',
                                              result_type='NUMBER',
                                              result_value=str(penalty))
