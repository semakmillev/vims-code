import datetime
import gc

from vims_code.app import ApplicationException, engine
from vims_code.models.game_author_list import GameAuthorList
from vims_code.models.game_list import GameList
import vims_code.game as gm
from vims_code.models.level_list import LevelList
from vims_code.game.game import games, Game
from vims_code.models.player_game_2_team import PlayerGame2Team
from vims_code.models.team_player_role_list import TeamPlayerRoleList
from vims_code.urls.admin.api import admin_routes, check_author
from vims_code.urls.api import ActionRequest


@admin_routes.post("/server/api/admin.create_game")
async def create_game(caption: str, action_request: ActionRequest):
    game_id = await GameList(action_request.conn).set(caption=caption, game_state='WORKING',
                                                      creation_date=datetime.datetime.now())
    gal = GameAuthorList(action_request.conn)
    player_id = action_request.player_id
    await gal.set(game_id=game_id, author_id=action_request.player_id, author_role='CREATOR')
    res = dict(
        player_team_roles=await TeamPlayerRoleList(action_request.conn).select_player_team_info(player_id),
        player_games=await PlayerGame2Team(action_request.conn).select_player_games(player_id),
        author_games=await GameAuthorList(action_request.conn).select_author_games(author_id=player_id))
    return res


@admin_routes.post("/server/api/admin.save_game")
async def save_game(game: {}, action_request: ActionRequest):
    await check_author(action_request.conn, action_request.player_id, game_id=game['id'])
    del game['registered_teams']
    del game['accepted_teams']
    await GameList(action_request.conn).set(**game)


@admin_routes.post("/server/api/admin.run_game")
async def run_game(game: {}, action_request: ActionRequest):
    game_id = int(game['id'])
    empty_levels = await LevelList(action_request.conn).level_with_empty_inner_id(game_id=game_id)
    if len(empty_levels) > 0:
        raise ApplicationException(43, 'Не у всех уровней заполнен идентификатор!')
    await check_author(action_request.conn, action_request.player_id, game_id=game['id'])
    gl = GameList(action_request.conn)
    game['game_state'] = 'STARTING'
    await gl.set(**game)
    await action_request.conn.commit()
    try:
        game['game_state'] = 'STARTED'
        current_game = gm.Game(engine, int(game['id']))
        current_game.game_yaml = await current_game.get_game_yaml()
        games[int(game['id'])] = current_game
        await current_game.start_game()
        # current_game.load_teams()
        await gl.set(**game)
    except Exception:
        await action_request.conn.rollback()
        game['game_state'] = 'WORKING'
        await gl.set(**game)
        await action_request.conn.commit()
        raise


@admin_routes.post("/server/api/admin.return_game", )
async def return_game(game: {}, action_request: ActionRequest):
    game_id = int(game['id'])
    await check_author(action_request.conn, action_request.player_id, game_id=game['id'])
    gl = GameList(action_request.conn)
    game['game_state'] = 'WORKING'
    await gl.set(**game)

    await clear_game(game, action_request)
    if int(game_id) in games:
        if games[int(game_id)].timer_task:
            games[int(game_id)].timer_task.cancel()
        if games[int(game_id)].game_connection:
            await games[int(game_id)].game_connection.close()
        del games[int(game_id)]
    await gl.set(**game)
    gc.collect()


@admin_routes.post("/server/api/admin.finish_game")
async def finish_game(game: {}, action_request: ActionRequest):
    game_id = game['id']
    await check_author(action_request.conn, action_request.player_id, game_id=game['id'])
    gl = GameList(action_request.conn)
    game['game_state'] = 'FINISHED'
    current_game = games[int(game['id'])]
    await current_game.finish_game()
    # current_game.load_teams()
    await gl.set(**game)
    del games[int(game_id)]
    gc.collect()


@admin_routes.post("/server/api/admin.clear_game")
async def clear_game(game: {}, action_request: ActionRequest):
    game_id = int(game['id'])
    await check_author(action_request.conn, action_request.player_id, game_id=game['id'])
    await Game.clear(game_id, action_request.conn)
