import sys

sys.path.append('vims-code')
import asyncio
import aiohttp
from aiohttp import web
# пул соединений с БД
from vims_code.app import engine, logger
from vims_code.app.server import create_app
import vims_code.game as gm

# В проекте вообще нет логгирования, т.к. пока не очень ясно, как его реализовывать.
from vims_code.models.game_list import GameList
from vims_code.urls import LIST_OF_ROUTES
from aiohttp_swagger import swagger_path, setup_swagger
from packaging import version

async def start_games():
    async with engine.connect() as conn:
        for row in await GameList(conn).select(game_state='STARTED'):
            game = gm.Game(engine, game_id=int(row['id']))
            gm.game.games[int(row['id'])] = game
            game.game_yaml = await game.get_game_yaml()
            await game.start_game()


def run():
    app = create_app()
    for r in LIST_OF_ROUTES:
        app.add_routes(r)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(start_games())
    setup_swagger(
        app,
        swagger_from_file="vims_code/swagger3.yaml",
        ui_version=3,
        swagger_url="/docs",
    )
    logger.info('http://0.0.0.0:7001/docs')

    if version.parse(aiohttp.__version__) >= version.parse('3.8'):
        web.run_app(app, port=7001, loop=loop)
    else:
        web.run_app(app, port=7001)



if __name__ == '__main__':
    run()
