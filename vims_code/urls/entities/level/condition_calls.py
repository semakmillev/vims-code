from vims_code.models.level_condition_list import LevelConditionList
from vims_code.urls.admin import check_author
from vims_code.urls.api import ActionRequest
from vims_code.urls.entities import entity_routes


@entity_routes.get('/server/admin/level/condition_list')
async def get_level_condition_list(level_id, action_request: ActionRequest):
    await check_author(action_request.conn, action_request.player_id, level_id=level_id)
    condition_list = await LevelConditionList(action_request.conn).select(level_id=level_id)

    return condition_list


@entity_routes.get('/server/admin/level/condition')
async def get_level_condition(id, action_request: ActionRequest):
    condition = await LevelConditionList(action_request.conn).get(id)
    await check_author(action_request.conn, action_request.player_id, level_id=condition['level_id'])
    return condition


@entity_routes.post('/server/admin/level/create_condition')
async def create_level_condition(level_id,
                                 condition_code,
                                 condition_type,
                                 condition_value,
                                 is_fail=0, action_request: ActionRequest = None):
    await check_author(action_request.conn, action_request.player_id, level_id=level_id)
    condition = await LevelConditionList(action_request.conn).set(
        level_id=level_id,
        condition_code=condition_code,
        condition_type=condition_type,
        condition_value=condition_value,
        is_fail=is_fail)

    return condition['id']


@entity_routes.post('/server/admin/set_condition')
async def set_level_condition(id,
                              level_id,
                              condition_code,
                              condition_type,
                              condition_value,
                              is_fail=0, action_request: ActionRequest = None):
    await check_author(action_request.conn, action_request.player_id, level_id=level_id)
    condition = await LevelConditionList(action_request.conn).set(id=id,
                                                                  level_id=level_id,
                                                                  condition_code=condition_code,
                                                                  condition_type=condition_type,
                                                                  condition_value=condition_value,
                                                                  is_fail=is_fail)

    return condition['id']


@entity_routes.post('/server/admin/delete_condition')
async def set_level_condition(condition_id, action_request: ActionRequest):
    c = await LevelConditionList(action_request.conn).get(condition_id)
    await check_author(action_request.conn, action_request.player_id, level_id=c['level_id'])
    await LevelConditionList(action_request.conn).delete(condition_id)
