from vims_code.models.info_condition_list import InfoConditionList
from vims_code.models.info_list import InfoList
from vims_code.urls.admin import check_author
from vims_code.urls.api import ActionRequest
from vims_code.urls.entities import entity_routes


@entity_routes.get('/server/admin/level/infos')
async def get_level_infos(level_id, action_request: ActionRequest):
    await check_author(action_request.conn, action_request.player_id, level_id=level_id)
    infos = await InfoList(action_request.conn).select(level_id=level_id)
    return infos


@entity_routes.get('/server/admin/level/info')
async def get_info(info_id, action_request: ActionRequest):
    info = await InfoList(action_request.conn).get(info_id)
    return info


@entity_routes.post('/server/admin/level/create_info')
async def create_info(
        level_id,
        inner_id=None,
        info_caption=None,
        info_text=None,
        condition_script=None,
        info_type='SIMPLE',
        level_link=None,
        action_request: ActionRequest = None):
    await check_author(action_request.conn, action_request.player_id, level_id=level_id)
    info = await InfoList(action_request.conn).create(level_id=level_id,
                                                      inner_id=inner_id,
                                                      info_caption=info_caption,
                                                      info_text=info_text,
                                                      condition_script=condition_script,
                                                      info_type=info_type,
                                                      level_link=level_link
                                                      )
    return info['id']


@entity_routes.post('/server/admin/level/set_info')
async def set_info(id,
                   level_id,
                   inner_id=None,
                   info_caption=None,
                   info_text=None,
                   condition_script=None,
                   info_type='SIMPLE',
                   level_link=None,
                   action_request: ActionRequest = None):
    await check_author(action_request.conn, action_request.player_id, level_id=level_id)
    info = await InfoList(action_request.conn).create(id=id,
                                                      level_id=level_id,
                                                      inner_id=inner_id,
                                                      info_caption=info_caption,
                                                      info_text=info_text,
                                                      condition_script=condition_script,
                                                      info_type=info_type,
                                                      level_link=level_link
                                                      )
    return info['id']


@entity_routes.post('/server/admin/level/delete_info')
async def delete_info(info_id, action_request: ActionRequest):
    info = await InfoList(action_request.conn).get(info_id)
    await check_author(action_request.conn, action_request.player_id, level_id=info['level_id'])
    await InfoList(action_request.conn).delete(info_id)
    await InfoConditionList(action_request.conn).delete_by_info(info_id)
