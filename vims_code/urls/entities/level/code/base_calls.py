from vims_code.models.code_list import CodeList
from vims_code.models.code_result_value_list import CodeResultValueList
from vims_code.models.level_list import LevelList
from vims_code.urls.admin import check_author
from vims_code.urls.api import ActionRequest
from vims_code.urls.entities import entity_routes


@entity_routes.get('/server/admin/level/code')
async def get_code(code_id, action_request: ActionRequest):
    code = await CodeList(action_request.conn).get(code_id)
    await check_author(action_request.conn, action_request.player_id, level_id=code['level_id'])
    return code


@entity_routes.post('/server/admin/level/create_code')
async def create_code(level_id,
                      caption=None,
                      code_inner_id=None,
                      code_type='SIMPLE',
                      code_tags=None,
                      code_values_info=None,
                      action_request: ActionRequest = None):
    await check_author(action_request.conn, action_request.player_id, level_id=level_id)
    code = await CodeList(action_request.conn).create(caption=caption,
                                                      level_id=level_id,
                                                      code_inner_id=code_inner_id,
                                                      code_type=code_type,
                                                      code_tags=code_tags,
                                                      code_values_info=code_values_info
                                                      )
    return code['id']


@entity_routes.post('/server/admin/level/set_code')
async def set_code(id,
                   level_id,
                   caption=None,
                   code_inner_id=None,
                   code_type='SIMPLE',
                   code_tags=None,
                   code_values_info=None,
                   action_request: ActionRequest = None):
    await check_author(action_request.conn, action_request.player_id, level_id=level_id)
    code = await CodeList(action_request.conn).create(id=id,
                                                      caption=caption,
                                                      level_id=level_id,
                                                      code_inner_id=code_inner_id,
                                                      code_type=code_type,
                                                      code_tags=code_tags,
                                                      code_values_info=code_values_info
                                                      )


@entity_routes.post('/server/admin/level/delete_code')
async def delete_code(code_id, action_request: ActionRequest):
    code = await CodeList(action_request.conn).get(code_id)
    await check_author(action_request.conn, action_request.player_id, level_id=code['level_id'])
    await CodeList(action_request.conn).delete(code_id)
    await CodeResultValueList(action_request.conn).delete_by_code(code_id)


@entity_routes.get('/server/admin/level/codes')
async def get_level_codes(level_id, action_request: ActionRequest):
    await check_author(action_request.conn, action_request.player_id, level_id=level_id)
    codes = await CodeList(action_request.conn).select_by_level(level_id)
    return codes
