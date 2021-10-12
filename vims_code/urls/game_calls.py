from aiohttp import web



from vims_code.game.game import games
from vims_code.game.levels import LevelBlockedException
from vims_code.urls.api import ActionRequest
from vims_code.utils.decorators import need_team_auth

game_routes = web.RouteTableDef()


@need_team_auth
@game_routes.post('/server/api/game.enter')
async def enter_game(action_request: ActionRequest):
    await action_request.player_auth.accept_invitation(
        action_request.player_id,
        action_request.team_id,
        action_request.game_id,
        action_request.game_token)


@need_team_auth
@game_routes.get('/server/api/game.team_info')
async def get_current_levels(action_request: ActionRequest):
    team = games[int(action_request.game_id)].team_dict[int(action_request.team_id)]
    team.conn = action_request.conn
    team_info = team.json_info()
    if team_info.get("finished", 0) == 1:
        team_info['level_summary'] = []
        for game_level in team.game_levels.values():
            team_info['level_summary'].append(game_level.json_info())
    team.conn = None
    return team_info


@need_team_auth
@game_routes.post('/server/api/game.send_code')
async def send_code(code_value: str, level_inner_id: str, code_type: str = 'SIMPLE',
                    action_request: ActionRequest = None):
    game_id = action_request.game_id
    team_id = action_request.team_id

    print(f'Received code {code_value}, team: {team_id}')
    team = games[game_id].team_dict[int(team_id)]
    # team.conn = action_request.conn
    if team.team_scores.check_level_blocked(level_inner_id):
        raise LevelBlockedException(43, 'Уровень заблокирован!')
    done_codes = team.do_code(level_inner_id=level_inner_id, code_value=code_value, code_type=code_type)
    code_info = [{"code_caption": done_code.caption, "code_value": code_value} for done_code in done_codes]

    team_info = team.json_info()
    if team_info.get("finished", 0) == 1:
        team_info['level_summary'] = []
        for game_level in team.game_levels.values():
            team_info['level_summary'].append(game_level.json_info())
    action = "accepted"
    res = {"code_info": code_info, "team_info": team_info, "action": action}
    # pprint(res)
    team.conn = None
    return res
