from vims_code.models.level_result_value_list import LevelResultValueList
from vims_code.urls.admin import check_author
from vims_code.urls.api import ActionRequest
from vims_code.urls.entities import entity_routes


@entity_routes.get('/server/admin/level/result_list')
async def get_level_result_list(level_id, action_request: ActionRequest):
    await check_author(action_request.conn, action_request.player_id, level_id=level_id)
    result_list = await LevelResultValueList(action_request.conn).select(level_id=level_id)

    return result_list


@entity_routes.get('/server/admin/level/result')
async def get_level_result(id, action_request: ActionRequest):
    result = await LevelResultValueList(action_request.conn).get(id)
    await check_author(action_request.conn, action_request.player_id, level_id=result['level_id'])
    return result


@entity_routes.post('/server/admin/level/create_result')
async def create_level_result(level_id,
                              result_code,
                              result_type,
                              result_value,
                              is_fail=0, action_request: ActionRequest = None):
    await check_author(action_request.conn, action_request.player_id, level_id=level_id)
    result = await LevelResultValueList(action_request.conn).set(
        level_id=level_id,
        result_code=result_code,
        result_type=result_type,
        result_value=result_value,
        is_fail=is_fail)

    return result['id']


@entity_routes.post('/server/admin/set_result')
async def set_level_result(id,
                           level_id,
                           result_code,
                           result_type,
                           result_value,
                           is_fail=0, action_request: ActionRequest = None):
    await check_author(action_request.conn, action_request.player_id, level_id=level_id)
    result = await LevelResultValueList(action_request.conn).set(id=id,
                                                                 level_id=level_id,
                                                                 result_code=result_code,
                                                                 result_type=result_type,
                                                                 result_value=result_value,
                                                                 is_fail=is_fail)

    return result['id']


@entity_routes.post('/server/admin/delete_result')
async def set_level_result(result_id, action_request: ActionRequest):
    r = await LevelResultValueList(action_request.conn).get(result_id)
    await check_author(action_request.conn, action_request.player_id, level_id=r['level_id'])
    await LevelResultValueList(action_request.conn).delete(result_id)
