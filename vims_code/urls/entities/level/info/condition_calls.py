from vims_code.models.info_condition_list import InfoConditionList
from vims_code.models.info_list import InfoList
from vims_code.urls.admin import check_author
from vims_code.urls.api import ActionRequest
from vims_code.urls.entities import entity_routes


@entity_routes.get('/server/admin/level/info/condition_list')
async def get_level_condition_list(level_id, action_request: ActionRequest):
    await check_author(action_request.conn, action_request.player_id, level_id=level_id)
    condition_list = await InfoConditionList(action_request.conn).select(level_id=level_id)

    return condition_list


@entity_routes.get('/server/admin/level/info/condition')
async def get_info_condition(id, action_request: ActionRequest):
    condition = await InfoConditionList(action_request.conn).get(id)
    info = await InfoList(action_request.conn).get(condition['info_id'])
    await check_author(action_request.conn, action_request.player_id, level_id=info['level_id'])
    return condition


@entity_routes.post('/server/admin/level/info/create_condition')
async def create_info_condition(info_id,
                                condition_code,
                                condition_type,
                                condition_value,
                                action_request: ActionRequest = None):
    info = await InfoList(action_request.conn).get(info_id)
    await check_author(action_request.conn, action_request.player_id, level_id=info['level_id'])
    condition = await InfoConditionList(action_request.conn).set(
        info_id=info_id,
        condition_code=condition_code,
        condition_type=condition_type,
        condition_value=condition_value)

    return condition['id']


@entity_routes.post('/server/admin/level/info/set_condition')
async def set_level_condition(id,
                              info_id,
                              condition_code,
                              condition_type,
                              condition_value, action_request: ActionRequest = None):
    info = await InfoList(action_request.conn).get(info_id)
    await check_author(action_request.conn, action_request.player_id, level_id=info['level_id'])
    condition = await InfoConditionList(action_request.conn).set(
        id=id,
        info_id=info_id,
        condition_code=condition_code,
        condition_type=condition_type,
        condition_value=condition_value)

    return condition['id']


@entity_routes.post('/server/admin/level/info/delete_condition')
async def delete_level_condition(condition_id, action_request: ActionRequest):
    condition = await InfoConditionList(action_request.conn).get(condition_id)
    info = await InfoList(action_request.conn).get(condition['info_id'])
    await check_author(action_request.conn, action_request.player_id, level_id=info['level_id'])
    await InfoConditionList(action_request.conn).delete(condition_id)
