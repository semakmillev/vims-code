from vims_code.models.game_author_list import GameAuthorList
from vims_code.models.game_list import GameList
from vims_code.models.level_list import LevelList
from vims_code.urls.admin import check_author
from vims_code.urls.api import ActionRequest
from vims_code.urls.entities import entity_routes


@entity_routes.get('/server/admin/game')
async def get_game(game_id, action_request: ActionRequest):
    game_id = int(game_id)
    await check_author(game_id=game_id, player_id=action_request.player_id, conn=action_request.conn)
    g = await GameList(action_request.conn).get(game_id)
    g['creation_date'] = g['creation_date'].strftime('%Y-%m-%dT%H:%M:%S')
    return g


@entity_routes.post('/server/admin/create_game')
async def create_game(caption, action_request: ActionRequest):
    # game_id = int(game_id)
    # await check_author(game_id=game_id, player_id=action_request.player_id, conn=action_request.conn)
    game_id = await GameList(action_request.conn).create(caption=caption)
    await GameAuthorList(action_request.conn).set(
        game_id=game_id,
        author_id=action_request.player_id,
        author_role="CREATOR"
    )
    return game_id


@entity_routes.post('/server/admin/set_game')
async def set_game(id,
                   game_state,
                   game_type,
                   caption,
                   game_yaml,
                   creation_date,
                   action_request: ActionRequest):
    # game_id = int(game_id)
    # await check_author(game_id=game_id, player_id=action_request.player_id, conn=action_request.conn)
    game_id = await GameList(action_request.conn).set(id=id,
                                                      game_state=game_state,
                                                      game_type=game_type,
                                                      caption=caption,
                                                      game_yaml=game_yaml,
                                                      creation_date=creation_date)

    return game_id


@entity_routes.post('/server/admin/set_game_yaml')
async def set_yaml(game_id, script_type, action_request: ActionRequest = None):
    res = "уровни:\n"
    level_list = await LevelList(action_request.conn).select_game_levels(game_id=game_id)
    if script_type == 'line':
        for level in sorted(level_list, key=lambda el: (el['inner_id'], el['id'])):
            res += "  - id: '" + level['inner_id'] + "'\n"
            res += "    порядок: 1\n"
    if script_type == 'sturm':
        for level in sorted(level_list, key=lambda el: (el['inner_id'], el['id'])):
            res += "  - id: '" + level['inner_id'] + "'\n"
            res += "    порядок: 0\n"
    await GameList(action_request.conn).set(id=game_id,
                                            game_yaml=res)
