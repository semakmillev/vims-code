from vims_code.auth.exceptions import SafetyFail
# from vims_code.models.code_condition_list import CodeConditionList
from vims_code.models.code_list import CodeList
from vims_code.models.code_result_value_list import CodeResultValueList
from vims_code.models.game_author_list import GameAuthorList
from vims_code.models.game_list import GameList
from vims_code.models.game_team_info import GameTeamInfo
from vims_code.models.info_condition_list import InfoConditionList
from vims_code.models.info_list import InfoList

from vims_code.models.level_list import LevelList

from vims_code.models.variable_list import VariableList
from vims_code.db_adapters.code_adapter import CodeAdapter
import vims_code.game as gm
from vims_code.game import Level
from vims_code.game.codes import Code
from vims_code.game.game import games
from vims_code.game.team import Team
from vims_code.urls.admin.api import admin_routes, check_author
from vims_code.urls.api import ActionRequest


def nvl(v):
    return v if v else ''


@admin_routes.get("/server/api/admin.game_info")
async def get_game_info(game_id: int, action_request: ActionRequest = None) -> {}:
    game_id = int(game_id)
    gla = GameAuthorList(action_request.conn)
    if len(await gla.select(game_id=game_id, author_id=action_request.player_id)) == 0:
        raise SafetyFail("Вы не являетесь автором этой игры!")
    gl = GameList(action_request.conn)
    game_info = await gl.get(game_id)
    gti = GameTeamInfo(action_request.conn)
    del game_info['creation_date']
    game_info["accepted_teams"] = await gti.select_game_teams(game_id=game_id, accepted=1)
    game_info["registered_teams"] = await gti.select_game_teams(game_id=game_id, accepted=0)
    return game_info


@admin_routes.get("/server/api/admin.level_infos")
async def get_level_infos(level_id: int, action_request: ActionRequest = None) -> {}:
    level_id = int(level_id)
    await check_author(action_request.conn, action_request.player_id, level_id)
    game_id = (await LevelList(action_request.conn).select(id=level_id))[0]['game_id']
    il = InfoList(action_request.conn)
    info_list = await il.select(level_id=level_id)
    icl = InfoConditionList(conn=action_request.conn)
    condition_list = {}
    variables = {row['variable_code']: row['variable_type'] for row in
                 await VariableList(action_request.conn).select_game_vars(game_id)}
    for info in info_list:
        info_id = info['id']
        info['conditions'] = {}
        for info_condition in await icl.select(info_id=info_id):
            info['conditions'][info_condition['condition_code']] = info_condition
            condition_list[info_condition['condition_code']] = info_condition['condition_type']
    info_list = list(sorted(info_list, key=lambda el: (el['inner_id'] or '',
                                                       el['info_caption'] or '')))
    return dict(condition_list=condition_list, info_list=info_list, variables=variables)


@admin_routes.post("/server/api/admin.save_level_info")
async def save_level_info(info: {}, level_id: int, action_request: ActionRequest = None) -> {}:
    game_id = await check_author(action_request.conn, action_request.player_id, level_id)
    info_id = info.get('id', None)
    level_id = int(level_id)
    prev_info = {}
    il = InfoList(action_request.conn)
    info_id = await il.set(id=info_id,
                           level_id=level_id,
                           inner_id=info.get('inner_id', None),
                           info_caption=info.get('info_caption', None),
                           info_text=info.get('info_text', None),
                           condition_script=info.get('condition_script', None))
    # ca = CodeAdapter(action_request.conn)
    icl = InfoConditionList(conn=action_request.conn)

    """

    if 'deleted_conditions' in info:
        for condition in info.get('deleted_conditions'):
            if condition == 'BY_REQUEST':
                ca.delete_code(ca.get_code_by_inner_id(condition['condition_value'].split(':')[0]))
            icl.delete(condition['id'])
    """
    await icl.delete_by_info(info_id)
    for condition in info['conditions'].values():
        """
        if condition == 'BY_REQUEST':
            code_inner_id = condition['condition_value'].split(":")[0]
            penalty = int(condition['condition_value'].split(":")[1])
            ca.set_by_request_code(code_inner_id, info.get('inner_id', None), penalty, level_id)
            # condition_id = condition.get('id', None)
            # old_condition = icl.select(id=condition_id)[0]
            # old_value = old_condition['condition_value']
        """
        condition['info_id'] = info_id
        await icl.set(**condition)
    ll = LevelList(action_request.conn)
    if game_id in games:
        game = games[game_id]

        # загрузим уровень

        updated_level = await game.reload_level(level_id, action_request.conn)
        # вуду-магия. Нужна чтобы считали в одной транзакции, а играли - в другой.
        updated_level.conn = game.game_connection
        game.level_dict[updated_level.inner_id] = updated_level

        for team in game.team_dict.values():
            if updated_level.inner_id in team.current_level_dict:
                if info_id in team.team_scores.infos[updated_level.inner_id]:
                    # new_info = gm.Info.from_db(game.game_connection, info_id)
                    team.team_scores.infos[updated_level.inner_id][info_id] = updated_level.info_dict[info_id]
    return info_id


@admin_routes.post("/server/api/admin.set_codes")
async def set_codes(code_list: [], result_list: {}, condition_list: {}, param_list: {}, deleted_codes: [], level_id,
                    action_request: ActionRequest = None):
    game_id = await check_author(action_request.conn, action_request.player_id, level_id)
    ca = CodeAdapter(action_request.conn)
    # добавить проверку принадлежности айдюков.
    code_list = await ca.code_list.multi_set(code_list, level_id)
    code_params = {}
    code_results = {}
    code_conditions = {}
    for code in code_list:
        for code_attribute in code:
            if code.get(code_attribute) is None:
                continue

            if str(code_attribute).startswith('PAR_'):
                param_code = code_attribute[4:]
                param_value = code[code_attribute]
                key = tuple([code['id'], param_code.split('|')[0]])
                code_params[key] = {'id': None,
                                    'code_id': code['id'],
                                    'param_code': param_code.split('|')[0],
                                    'param_type': param_code.split('|')[1],
                                    'param_value': param_value}
                await ca.code_param_value_list.multi_set(list(code_params.values()))
            if str(code_attribute).startswith('RES_'):
                result_code = code_attribute[4:]
                result_value = code[code_attribute]
                key = tuple([code['id'], result_code.split('|')[0]])
                code_results[key] = {'id': None,
                                     'code_id': code['id'],
                                     'result_code': result_code.split('|')[0],
                                     'result_type': result_code.split('|')[1],
                                     'result_value': result_value}
                await ca.code_result_value_list.multi_set(list(code_results.values()))
            if str(code_attribute).startswith('CON_'):
                condition_code = code_attribute[4:]
                condition_value = code[code_attribute]
                key = tuple([code['id'], condition_code.split('|')[0]])
                code_conditions[key] = {'id': None,
                                        'code_id': code['id'],
                                        'condition_code': condition_code.split('|')[0],
                                        'condition_type': condition_code.split('|')[1],
                                        'condition_value': condition_value}
                await ca.code_result_value_list.multi_set(list(code_conditions.values()))
    for code in deleted_codes:
        code_inner_id = code.get('code_inner_id')
        if code_inner_id:
            # await ca.clear_code_links(code_inner_id, level_id)
            await ca.delete_code(code['id'])
    if game_id in games:
        game = games[game_id]
        updated_level: Level = await game.reload_level(level_id, action_request.conn)
        # вуду-магия. Нужна чтобы считали в одной транзакции, а играли - в другой.
        updated_level.conn = game.game_connection
        game.level_dict[updated_level.inner_id] = updated_level

        for t in game.team_dict.values():
            team: Team = t
            for code_row in code_list:
                code_id = code_row['id']
                code = updated_level.codes[code_id]
                if code_id in team.done_codes:
                    team.team_scores.change_code_result(code, updated_level.inner_id)

    return list(map(lambda el: el['id'], code_list))
    '''
    return
    for code in code_list:
        print(code, type(code))
        if code.get('code_inner_id') is None and code.get('id') is None and code.get('code_values_info') is None:
            continue

        code_id = ca.code_list.set(id=code.get('id'),
                                   caption=code.get('caption'),
                                   code_type=code.get('code_type'),
                                   code_tags=code.get('code_tags'),
                                   code_values_info=code.get('code_values_info'),
                                   code_inner_id=code.get('code_inner_id'),
                                   level_id=level_id)
        code['id'] = code_id
        ca.code_value_list.delete_by_code(code_id)
        try:
            for code_value in code.get('code_values_info').split('|'):
                ca.code_value_list.set(code_id=code_id, value_type='SIMPLE', code_value=code_value)
        except AttributeError:
            pass
        ca.code_param_value_list.delete_by_code(code_id)
        ca.code_result_value_list.delete_by_code(code_id)
        ca.code_param_value_list.delete_by_code(code_id)
        ca.code_condition_list.delete_by_code(code_id)
        for code_attribute in code:
            if code.get(code_attribute) is None:
                continue
            if str(code_attribute).startswith('PAR_'):
                param_code = code_attribute[4:]
                param_value = code[code_attribute]
                ca.code_param_value_list.set(code_id=code_id,
                                             param_code=param_code.split('|')[0],
                                             param_type=param_code.split('|')[1],
                                             param_value=param_value)
            if str(code_attribute).startswith('RES_'):
                result_code = code_attribute[4:]
                result_value = code[code_attribute]
                ca.code_result_value_list.set(code_id=code_id,
                                              result_code=result_code.split('|')[0],
                                              result_type=result_code.split('|')[1],
                                              result_value=result_value)
            if str(code_attribute).startswith('CON_'):
                condition_code = code_attribute[4:]
                condition_value = code[code_attribute]
                ca.code_condition_list.set(code_id=code_id,
                                           condition_code=condition_code.split('|')[0],
                                           condition_type=condition_code.split('|')[1],
                                           condition_value=condition_value)
    for code in deleted_codes:
        code_inner_id = code.get('code_inner_id')
        if code_inner_id:
            ca.clear_code_links(code_inner_id, level_id)
            ca.delete_code(code['id'])
    if game_id in gm.games:
        game = gm.games[game_id]
        updated_level = gm.Level.init_level_from_db(game.game_connection, level_id)
        game.level_dict[updated_level.inner_id] = updated_level
        for t in game.team_dict.values():
            team: Team = t
            for code in code_list:
                code_id = code.code_id
                if code_id in team.done_codes:
                    team.team_scores.change_code_result(code, updated_level.inner_id)

    return list(map(lambda el: el['id'], code_list))
    '''


@admin_routes.post("/server/api/admin.delete_info")
async def delete_info(info_id: int, action_request: ActionRequest):
    il = InfoList(action_request.conn)
    level_id = (await il.get(id=info_id))['level_id']
    await check_author(action_request.conn, action_request.player_id, level_id)
    icl = InfoConditionList(action_request.conn)
    ca = CodeAdapter(action_request.conn)
    condition_list = await icl.select(id=info_id)
    for condition in condition_list:
        if condition == 'BY_REQUEST':
            await ca.delete_code(ca.get_code_by_inner_id(condition['condition_value'].split(':')[0]))
        await icl.delete(condition['id'])
    await il.delete(id=info_id)


@admin_routes.get("/server/api/admin.level_code_list")
async def level_code_list(level_id: int, action_request: ActionRequest):
    level_id = int(level_id)
    await check_author(action_request.conn, action_request.player_id, level_id)
    game_id = (await LevelList(action_request.conn).get(id=level_id))['game_id']
    cl = CodeList(action_request.conn)
    code_list = await cl.select_by_level(level_id=level_id)
    crvl = CodeResultValueList(action_request.conn)
    #
    # ccl = CodeConditionList(action_request.conn)
    # закомменченно до момента когда это действительно понадобится
    '''
    cpvl = CodeParamValueList(action_request.conn)
    param_list = {f"{p['param_code']}|{p['param_type']}": p['param_type'] for p in
                  await cpvl.get_level_param_list(level_id=level_id)}
    '''
    param_list = []
    result_list = {f"{r['result_code']}|{r['result_type']}": r['result_type'] for r in
                   await crvl.get_level_result_list(level_id=level_id)}

    # condition_list = {f"{r['condition_code']}|{r['condition_type']}": r['condition_type'] for r in
    #                  await ccl.get_code_condition_list_by_level(level_id=level_id)}
    condition_list = []
    results = await crvl.get_code_result_values_by_level(level_id=level_id)
    params = [] # await cpvl.get_code_param_values_by_level(level_id=level_id)
    # conditions = await ccl.get_code_condition_values_by_level(level_id=level_id)
    conditions = {}
    variables = {row['variable_code']: row['variable_type'] for row in
                 await VariableList(action_request.conn).select_game_vars(game_id)}

    conditions['TIME_FROM|SIMPLE'] = 'SIMPLE'
    conditions['TIME_TO|SIMPLE'] = 'SIMPLE'
    result_list['POINTS|SIMPLE'] = 'SIMPLE'

    for code in code_list:
        #for param in param_list:
        #    code['PAR_' + param] = param.get(code['id'], {param: None}).get(param, None)
        for result in result_list:
            code['RES_' + result] = results.get(code['id'], {result: None}).get(result, None)
        #for condition in condition_list:
        #    code['CON_' + condition] = condition.get(code['id'], {condition: None}).get(condition, None)
    code_list = list(sorted(code_list, key=lambda el: (nvl(el['code_inner_id']), el['id'])))
    return dict(result_list=result_list, param_list=param_list, condition_list=condition_list,
                code_list=code_list, variables=variables)

    # games[19] = game
    # game.start_game()


@admin_routes.post("/server/api/admin.change_team_game_state")
async def change_team_game_state(team_id, game_id, accepted, action_request: ActionRequest):
    team_id = int(team_id)
    game_id = int(game_id)
    gti = GameTeamInfo(conn=action_request.conn)

    await gti.change_state(team_id, game_id, accepted)
    gti = GameTeamInfo(action_request.conn)
    return dict(accepted_teams=await gti.select_game_teams(game_id=game_id, accepted=1),
                registered_teams=await gti.select_game_teams(game_id=game_id, accepted=0))


'''









    pass


@ActionRequest.register_action("admin.upload_files", needs_auth=True)
def upload_files(files, game_id, action_request: ActionRequest):
    print('!!!!!!!!!!!!!!!!!!!!!!!!')
    action_request = action_request.editing_game_id
    check_author(action_request.conn, action_request.player_id, game_id=game_id)
    print(files)

'''

'''
@ActionRequest.register_action("admin.change_team_game_state", needs_auth=True)
def change_team_game_state(team_id, game_id, accepted, action_request: ActionRequest):
    gti = GameTeamInfo(conn=action_request.conn)

    gti.change_state(team_id, game_id, accepted)
    gti = GameTeamInfo(action_request.conn)
    return dict(accepted_teams=gti.select_game_teams(game_id=game_id, accepted=1),
                registered_teams=gti.select_game_teams(game_id=game_id, accepted=0))

'''
