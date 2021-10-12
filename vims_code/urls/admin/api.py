from aiohttp import web
from sqlalchemy.ext.asyncio import AsyncConnection

from vims_code.auth.exceptions import SafetyFail
from vims_code.models.game_author_list import GameAuthorList
from vims_code.models.level_list import LevelList


async def check_author(conn: AsyncConnection, player_id, level_id=None, game_id=None):
    game_id = game_id if game_id else int((await LevelList(conn).get(id=int(level_id)))['game_id'])
    gla = GameAuthorList(conn)
    if len(await gla.select(game_id=game_id, author_id=player_id)) == 0:
        raise SafetyFail("Вы не являетесь автором этой игры!")
    return game_id


admin_routes = web.RouteTableDef()
