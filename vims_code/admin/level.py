from sqlalchemy.ext.asyncio import AsyncConnection

from vims_code.models.level_condition_list import LevelConditionList
from vims_code.models.level_list import LevelList
from vims_code.models.level_result_value_list import LevelResultValueList


async def get_levels_info(conn: AsyncConnection, level_id: int = None, game_id: int = None):
    ll = LevelList(conn)
    level_list = await ll.select(game_id=game_id, id=level_id)
    level_dict = {level['id']: level for level in level_list if level['level_type'] != 'DELETED'}
    if game_id is None:
        level_condition_list = await LevelConditionList(conn).select(level_id=level_id, is_fail=None)
    else:
        level_condition_list = await LevelResultValueList(conn).select_by_game(game_id=game_id)
    level_condition_by_level = {}
    for level_condition in level_condition_list:
        try:
            level_condition_by_level[level_condition['level_id']][level_condition['condition_code']] = level_condition
        except KeyError:
            level_condition_by_level[level_condition['level_id']] = {level_condition['condition_code']: level_condition}
    if game_id is None:
        level_result_value_list = await LevelResultValueList(conn).select(level_id=level_id, is_fail=None)
    else:
        level_result_value_list = await LevelResultValueList(conn).select_by_game(game_id=game_id)
    level_result_by_level = {}
    for level_result in level_result_value_list:
        try:
            level_result_by_level[level_result['level_id']][level_result['result_code']] = level_result
        except KeyError:
            level_result_by_level[level_result['level_id']] = {level_result['result_code']: level_result}

    for level_id in level_dict:
        level_dict[level_id]['level_conditions'] = level_condition_by_level.get(level_id, {})
        level_dict[level_id]['level_results'] = level_result_by_level.get(level_id, {})

    return level_dict
