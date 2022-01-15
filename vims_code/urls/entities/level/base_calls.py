from vims_code.models.code_list import CodeList
from vims_code.models.code_result_value_list import CodeResultValueList
from vims_code.models.info_condition_list import InfoConditionList
from vims_code.models.info_list import InfoList
from vims_code.models.level_condition_list import LevelConditionList
from vims_code.models.level_list import LevelList
from vims_code.models.level_result_value_list import LevelResultValueList
from vims_code.models.tick_list import TickList
from vims_code.models.tick_param_value_list import TickParamValueList
from vims_code.models.utils import group_by
from vims_code.urls.admin import check_author
from vims_code.urls.api import ActionRequest
from vims_code.urls.entities import entity_routes


@entity_routes.get('/server/admin/level')
async def get_level(level_id, action_request: ActionRequest):
    level = await LevelList(action_request.conn).get(level_id)
    return level


@entity_routes.post('/server/admin/create_level')
async def create_level(caption, game_id, inner_id=None, level_type='SIMPLE',
                       condition_script=None,
                       failed_condition_script=None,
                       action_request: ActionRequest = None):
    await check_author(action_request.conn, action_request.player_id, game_id=game_id)
    level = await LevelList(action_request.conn).create(caption=caption,
                                                        game_id=game_id,
                                                        level_type=level_type,
                                                        inner_id=inner_id,
                                                        condition_script=condition_script,
                                                        failed_condition_script=failed_condition_script
                                                        )

    tick_id = await TickList(action_request.conn).set(tick_type='LEVEL', level_id=level['id'])

    await TickParamValueList(action_request.conn).set(tick_id=tick_id,
                                                      param_code='DURATION',
                                                      param_type='SIMPLE',
                                                      param_value='1')
    await LevelConditionList(action_request.conn).set(level_id=level['id'],
                                                      condition_code='POINTS',
                                                      condition_type='>=',
                                                      condition_value='0',
                                                      is_fail=0)
    await LevelConditionList(action_request.conn).set(level_id=level['id'],
                                                      condition_code='DURATION',
                                                      condition_type='>=',
                                                      condition_value='60',
                                                      is_fail=1)
    return level['id']


@entity_routes.post('/server/admin/set_level')
async def set_level(id,
                    caption, game_id, inner_id=None, level_type='SIMPLE',
                    condition_script=None,
                    failed_condition_script=None,
                    action_request: ActionRequest = None):
    await check_author(action_request.conn, action_request.player_id, game_id=game_id)
    level = await LevelList(action_request.conn).create(id=id,
                                                        caption=caption,
                                                        game_id=game_id,
                                                        level_type=level_type,
                                                        inner_id=inner_id,
                                                        condition_script=condition_script,
                                                        failed_condition_script=failed_condition_script
                                                        )
    return level['id']


@entity_routes.post('/server/admin/delete_level')
async def delete_level(level_id, action_request: ActionRequest):
    await check_author(action_request.conn, action_request.player_id, level_id=level_id)
    await LevelList(action_request.conn).delete(level_id)


@entity_routes.get('/server/admin/game/levels')
async def get_game_levels(game_id, action_request: ActionRequest):
    await check_author(action_request.conn, action_request.player_id, game_id=game_id)
    levels = await LevelList(action_request.conn).select_game_levels(game_id)
    return levels


@entity_routes.get('/server/admin/game/level_full_info')
async def get_level_full_info(level_id, action_request: ActionRequest):
    level_id = int(level_id)
    # сам уровень
    await check_author(action_request.conn, action_request.player_id, level_id=level_id)
    level_info = await LevelList(action_request.conn).get(level_id)
    level_condition_list = await LevelConditionList(action_request.conn).select(level_id=level_id,
                                                                                is_fail=None)
    level_info['conditions'] = list(filter(lambda lcl: lcl['is_fail'] == 0, level_condition_list))
    level_info['failed_conditions'] = list(filter(lambda lcl: lcl['is_fail'] == 1, level_condition_list))

    level_results = await LevelResultValueList(action_request.conn).select(level_id=level_id)
    level_info['results'] = list(filter(lambda lr: lr['is_fail'] == 0, level_results))
    level_info['failed_results'] = list(filter(lambda lr: lr['is_fail'] == 1, level_results))
    # информация
    info_list = await InfoList(action_request.conn).select(level_id=level_id)
    info_condition_list = await InfoConditionList(action_request.conn).select(
        level_id=level_id
    )
    info_condition_dict = group_by(info_condition_list, 'info_id')
    for i in info_list:
        i['conditions'] = info_condition_dict.get(i['id'], [])
    level_info['info_list'] = info_list
    # коды
    code_list = await CodeList(action_request.conn).select_by_level(level_id=level_id)
    code_result_list = await CodeResultValueList(action_request.conn).select(level_id=level_id)
    code_results = group_by(code_result_list, "code_id")
    for code in code_list:
        code['code_result_values'] = code_results.get(code['id'], [])
    level_info['code_list'] = code_list
    return level_info
