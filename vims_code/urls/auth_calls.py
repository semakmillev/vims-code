
from aiohttp import web

from vims_code.app import ErrorCodes, ApplicationException
from vims_code.auth.exceptions import SafetyFail
from vims_code.auth.team_auth import TeamAuthClass
from vims_code.urls.api import ActionRequest
from vims_code.urls.info_calls import show_game_list
from vims_code.models.game_author_list import GameAuthorList
from vims_code.models.game_list import GameList
from vims_code.models.game_team_info import GameTeamInfo
from vims_code.models.player_game_2_team import PlayerGame2Team
from vims_code.models.team import DatabaseTeam
from vims_code.models.team_game_auth import TeamGameAuth
from vims_code.models.team_player_role_list import TeamPlayerRoleList
from vims_code.utils.decorators import white_list

"""
@ActionRequest.call_action("admin.full_search_objects")
def full_search_objects(object_id: int = None,
                        object_code: str = None,
                        object_type: str = None,
                        account_id: int = None,
                        owner_id: int = None,
                        creator_id: int = None):
    pass
"""

auth_routes = web.RouteTableDef()


@white_list
@auth_routes.post("/server/api/auth.register")
async def register_player(login: str = None,
                          pwd: str = None,
                          email: str = None,
                          action_request: ActionRequest = None) -> str:

    await action_request.player_auth.register_player(login=login, pwd=pwd, email=email)
    '''except ApplicationException as ae:
        raise ae
    except Exception as e:
        raise ApplicationException(ErrorCodes.OTHER, str(e))
        '''


@white_list
@auth_routes.post("/server/api/auth.login")
async def login_player(login: str = None,
                       pwd: str = None,
                       action_request: ActionRequest = None):
    return await action_request.player_auth.auth(login, pwd)


@auth_routes.post("/server/api/auth.create_team")
async def create_team(team_caption: str, action_request: ActionRequest = None):
    team_auth = TeamAuthClass(action_request.conn)
    team_id = await team_auth.create_team(action_request.player_id, team_caption)
    return team_id


@auth_routes.post("/server/api/auth.register_team_2_game")
async def register_team_2_game(team_id: int, game_id: int, action_request: ActionRequest = None):
    tprl = TeamPlayerRoleList(action_request.conn)
    if len(await tprl.select(team_id=team_id, player_id=action_request.player_id)) == 0:
        raise SafetyFail('Вы не можете подавать заявку от лица этой команды!')
    gti = GameTeamInfo(action_request.conn)
    registered_teams = await gti.get_player_team_registered(player_id=action_request.player_id, game_id=game_id)
    if registered_teams and len(registered_teams) > 0:
        team_name = registered_teams[0]['caption']
        team_id = registered_teams[0]['id']
        error_text = f"Вами (или кем-то из ваших соуправленцев) уже подана заявка на игру от {team_name} (id{team_id})"
        raise ApplicationException(43, error_text)
    await gti.set(game_id=game_id, team_id=team_id)
    return await show_game_list(action_request)


@auth_routes.post("/server/api/auth.generate_game_token")
async def generate_game_token(team_id: int, game_id: int, action_request: ActionRequest = None):
    team_auth = TeamAuthClass(action_request.conn)
    game_token = await team_auth.generate_token(game_id, team_id)
    return game_token


@auth_routes.post("/server/api/auth.init_game_token")
async def get_game_token(team_id: int, game_id: int, action_request: ActionRequest = None):
    tprl = TeamPlayerRoleList(action_request.conn)
    if len(await tprl.select(team_id=team_id, player_id=action_request.player_id, player_role='OWNER')) == 0:
        raise ApplicationException(43, 'Вы не можете получать ссылку на игру!')

    team_auth = TeamAuthClass(action_request.conn)
    game_token = await team_auth.get_game_token(game_id, team_id)
    if game_token is None:
        game_token = await team_auth.generate_token(game_id, team_id)
    return game_token


@auth_routes.post("/server/api/auth.accept_game")
async def accept_game(game_token: str, action_request: ActionRequest = None):
    await action_request.player_auth.accept_invitation(action_request.player_id, game_token)


@auth_routes.get("/server/api/auth.player_info")
async def player_game_list(player_id: int, action_request: ActionRequest):
    res = dict(
        player_team_roles=await TeamPlayerRoleList(action_request.conn).select_player_team_info(player_id),
        player_games=await PlayerGame2Team(action_request.conn).select_player_games(player_id),
        author_games=await GameAuthorList(action_request.conn).select_author_games(author_id=player_id))
    return res


@auth_routes.get("/server/api/auth.get_team_token_info")
async def get_team_token_info(token: str, action_request: ActionRequest):
    tga = TeamGameAuth(action_request.conn)

    rows = await tga.select(token=token, is_active=1)
    if len(rows) == 0:
        raise ApplicationException(43, 'Токен не валидный!')
    team_id = rows[0]['team_id']
    game_id = rows[0]['game_id']
    team_name = (await DatabaseTeam(action_request.conn).get(id=team_id))['caption']

    game_caption = (await GameList(action_request.conn).get(game_id))['caption']

    # gm.games[game_id].team_dict[team_id].tea
    return dict(team_id=team_id, game_id=game_id, game_caption=game_caption, team_name=team_name)
