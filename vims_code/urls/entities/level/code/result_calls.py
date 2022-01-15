from vims_code.models.code_list import CodeList
from vims_code.models.code_result_value_list import CodeResultValueList
from vims_code.models.level_result_value_list import LevelResultValueList
from vims_code.urls.admin import check_author
from vims_code.urls.api import ActionRequest
from vims_code.urls.entities import entity_routes


@entity_routes.get('/server/admin/level/code/result_value')
async def get_code_result_value(code_result_value_id, action_request: ActionRequest):
    result_value = await CodeResultValueList(action_request.conn).get(code_result_value_id)
    code = await CodeList(action_request.conn).get(result_value['code_id'])
    await check_author(action_request.conn, action_request.player_id, level_id=code['level_id'])
    return result_value


@entity_routes.get('/server/admin/level/code/result_value_list')
async def get_code_result_value_list(code_id, action_request: ActionRequest):
    code = await CodeList(action_request.conn).get(code_id)
    await check_author(action_request.conn, action_request.player_id, level_id=code['level_id'])
    result_values = CodeResultValueList(action_request.conn).select(code_id=code_id)
    return result_values


@entity_routes.post('/server/admin/level/code/create_result')
async def create_code_result_value(code_id,
                                   result_code,
                                   result_type,
                                   result_value,
                                   action_request: ActionRequest = None):
    code = await CodeList(action_request.conn).get(code_id)
    await check_author(action_request.conn, action_request.player_id, level_id=code['level_id'])

    result = await CodeResultValueList(action_request.conn).set(
        code_id=code_id,
        result_code=result_code,
        result_type=result_type,
        result_value=result_value)

    return result['id']


@entity_routes.post('/server/admin/level/code/set_result')
async def set_level_result(id,
                           code_id,
                           result_code,
                           result_type,
                           result_value,
                           action_request: ActionRequest = None):
    code = await CodeList(action_request.conn).get(code_id)
    await check_author(action_request.conn, action_request.player_id, level_id=code['level_id'])

    result = await CodeResultValueList(action_request.conn).set(
        id=id,
        code_id=code_id,
        result_code=result_code,
        result_type=result_type,
        result_value=result_value)

    return result['id']


@entity_routes.post('/server/admin/level/code/delete_result')
async def set_level_result(code_result_value_id, action_request: ActionRequest):
    result_value = await CodeResultValueList(action_request.conn).get(code_result_value_id)
    code = await CodeList(action_request.conn).get(result_value['code_id'])
    await check_author(action_request.conn, action_request.player_id, level_id=code['level_id'])
    await CodeResultValueList(action_request.conn).delete(code_result_value_id)

