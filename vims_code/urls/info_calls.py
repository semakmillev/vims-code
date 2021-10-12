from aiohttp import web

from vims_code.models.game_list import GameList
from vims_code.models.game_team_info import GameTeamInfo
from vims_code.urls.api import ActionRequest
from vims_code.utils.decorators import white_list

info_routes = web.RouteTableDef()


@white_list
@info_routes.get("/server/api/info.game_list")
async def show_game_list(action_request: ActionRequest = None):
    game_list = await GameList(action_request.conn).select()
    gti = GameTeamInfo(action_request.conn)

    res = []
    for g in game_list:
        game_info = {"game_id": g['id'],
                     "game_state": g['game_state'],
                     "caption": g['caption'],
                     "type": g['game_type'],
                     "accepted_teams": {row['id']: row['caption'] for row in
                                        await gti.select_game_teams(game_id=g['id'], accepted=1)},
                     "registered_teams": {row['id']: row['caption'] for row
                                          in await gti.select_game_teams(game_id=g['id'], accepted=0)}
                     }
        res.append(game_info)
    return res
