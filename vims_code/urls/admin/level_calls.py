from itertools import groupby


from vims_code.models.code_result_value_list import CodeResultValueList
from vims_code.models.level_condition_list import LevelConditionList
from vims_code.models.level_list import LevelList
from vims_code.models.level_result_value_list import LevelResultValueList
from vims_code.models.tick_list import TickList
from vims_code.models.tick_param_value_list import TickParamValueList
from vims_code.models.variable_list import VariableList
import vims_code.game as gm
from vims_code.game.game import games
from vims_code.urls.admin.api import admin_routes, check_author
from vims_code.admin import level as lv
from vims_code.urls.api import ActionRequest


@admin_routes.get("/server/api/admin.level_list")
async def level_list(game_id: int, action_request: ActionRequest = None) -> []:
    game_id = int(game_id)
    await check_author(action_request.conn, player_id=action_request.player_id, game_id=game_id)
    res = await lv.get_levels_info(action_request.conn, game_id=game_id)
    return res


@admin_routes.get("/server/api/admin.level")
async def get_game_info(level_id: int, action_request: ActionRequest = None) -> {}:
    level_id = int(level_id)
    await check_author(action_request.conn, action_request.player_id, level_id)
    res = (await admin.level.get_levels_info(action_request.conn, level_id=level_id)).get(level_id)
    return res


@admin_routes.get("/server/api/admin.get_level_full")
async def get_level_full_info(level_id: int, action_request: ActionRequest):
    level_id = int(level_id)
    await check_author(action_request.conn, action_request.player_id, level_id=level_id)
    level_info = await LevelList(action_request.conn).get(id=level_id)
    game_id = level_info['game_id']
    level_condition_list = await LevelConditionList(conn=action_request.conn).select(level_id=level_id, is_fail=0)
    level_condition_failed_list = await LevelConditionList(conn=action_request.conn).select(level_id=level_id,
                                                                                            is_fail=1)
    level_conditions = {level_condition['condition_code']: level_condition for level_condition in level_condition_list}
    level_failed_conditions = {level_condition['condition_code']: level_condition for level_condition in
                               level_condition_failed_list}
    code_result_value_list = await CodeResultValueList(action_request.conn).get_result_values_by_level(level_id)
    code_result_values = {}
    variables = {row['variable_code']: row['variable_type'] for row in
                 await VariableList(action_request.conn).select_game_vars(game_id)}
    bonuses_and_penalties = []
    for code_result_value in code_result_value_list:
        if variables.get(code_result_value['result_code'], 'TEXT') in ('NUMBER', 'TIME') \
                and code_result_value['result_type'] == 'SIMPLE':
            try:
                code_result_values[code_result_value['result_code']] += int(code_result_value['result_value'])
            except KeyError:
                code_result_values[code_result_value['result_code']] = int(code_result_value['result_value'])

    bonuses_and_penalties = []
    for key, grp in groupby(filter(lambda el: el['result_type'] in ('BONUS', 'PENALTY') and
                                              variables.get(el['result_code']) in ('NUMBER', 'TIME'),
                                   code_result_value_list),
                            lambda x: [x["result_code"], x["result_type"]]):
        temp_dict = dict(zip(["result_code", "result_type"], key))
        # print([item["result_value"] for item in grp])
        temp_dict["result_value"] = sum(int(item["result_value"]) for item in grp)
        bonuses_and_penalties.append(temp_dict)

    level_info['bonuses_and_penalties'] = bonuses_and_penalties
    level_info['variables'] = variables
    level_info['level_conditions'] = level_conditions
    level_info['level_failed_conditions'] = level_failed_conditions
    level_info['total_code_results'] = code_result_values
    from vims_code.models.level_result_value_list import LevelResultValueList
    level_info['level_results'] = {row['result_code']: row for row in
                                   await LevelResultValueList(action_request.conn).select(level_id=level_id, is_fail=0)}
    level_info['level_failed_results'] = {row['result_code']: row for row in
                                          await LevelResultValueList(action_request.conn).select(level_id=level_id,
                                                                                                 is_fail=1)}
    return level_info


@admin_routes.post("/server/api/admin.set_level_full")
async def set_level_info(level: {}, action_request: ActionRequest):
    game_id = int(level['game_id'])
    await check_author(action_request.conn, action_request.player_id, game_id=game_id)
    ll = LevelList(action_request.conn)
    level_id = int(await ll.set(**level))

    lcl = LevelConditionList(action_request.conn)
    lrvl = LevelResultValueList(action_request.conn)
    # await lcl.delete_by_level(level_id)
    # Vawait lrvl.delete_by_level(level_id)
    for level_condition in level['level_conditions'].values():
        level_condition['level_id'] = int(level_condition['level_id'])
        level_condition['is_fail'] = 0
        await lcl.set(**level_condition)
    for level_condition in level['level_failed_conditions'].values():
        level_condition['level_id'] = int(level_condition['level_id'])
        level_condition['is_fail'] = 1
        await lcl.set(**level_condition)
    for level_result in level['level_results'].values():
        level_result['level_id'] = int(level_condition['level_id'])
        level_result['is_fail'] = 0
        await lrvl.set(**level_result)
    for level_result in level['level_failed_results'].values():
        level_result['level_id'] = int(level_condition['level_id'])
        level_result['is_fail'] = 1
        await lrvl.set(**level_result)
    if game_id in games:
        game = games[game_id]
        game.level_dict[level['inner_id']] = await gm.Level.init_level_from_db(game.game_connection, level_id)
        for team in game.team_dict.values():
            team.team_scores.change_level_result(game.level_dict[level['inner_id']])
    return level_id


@admin_routes.post("/server/api/admin.save_levels")
async def save_levels(level_list: [], action_request: ActionRequest = None) -> []:
    # check_author(action_request.conn, player_id=action_request.player_id, game_id=game_id)
    # res = admin.level.get_levels_info(action_request.conn, game_id=game_id)
    ll = LevelList(action_request.conn)
    for level in level_list:
        await check_author(action_request.conn, player_id=action_request.player_id, game_id=level['game_id'])
        del level['level_conditions']
        del level['level_results']
        await ll.set(**level)


@admin_routes.post("/server/api/admin.add_levels")
async def add_levels(num_of_levels: int, game_id: int, action_request: ActionRequest):
    num_of_levels = int(num_of_levels)
    game_id = int(game_id)
    await check_author(action_request.conn, action_request.player_id, game_id=game_id)
    ll = LevelList(action_request.conn)
    for i in range(0, num_of_levels):
        level_id = await ll.set(game_id=game_id)
        tick_id = await TickList(action_request.conn).set(tick_type='LEVEL', level_id=level_id)
        await TickParamValueList(action_request.conn).set(tick_id=tick_id,
                                                          param_code='DURATION',
                                                          param_type='SIMPLE',
                                                          param_value='1')
        await LevelConditionList(action_request.conn).set(level_id=level_id,
                                                          condition_code='POINTS',
                                                          condition_type='>=',
                                                          condition_value='0',
                                                          is_fail=0)
        await LevelConditionList(action_request.conn).set(level_id=level_id,
                                                          condition_code='DURATION',
                                                          condition_type='>=',
                                                          condition_value='60',
                                                          is_fail=1)
    return await level_list(game_id, action_request)  # action_request.call_action("admin.level_list", game_id=game_id)


@admin_routes.post("/server/api/admin.delete_level")
async def add_levels(level_id: int, action_request: ActionRequest):
    await LevelList(action_request.conn).set(id=level_id, level_type='DELETED')
