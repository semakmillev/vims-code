from aiohttp import web
from aiohttp_middlewares import cors_middleware

from vims_code.app.middlewares import error_middleware, main_middleware, params_middleware


GIGABYTE = 1024 ** 3


def create_app():
    app = web.Application(
        client_max_size=GIGABYTE * 4,
        middlewares=[
            cors_middleware(
                allow_all=True, allow_credentials=True, allow_headers=["*"]
            ),
            error_middleware,
            main_middleware,
            params_middleware,
        ],
    )

    return app