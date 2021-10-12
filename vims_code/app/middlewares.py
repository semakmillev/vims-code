import os
from http import HTTPStatus

from aiofile import async_open
from aiohttp import web
from aiohttp.web import HTTPException, json_response, middleware
from aiohttp.web_request import Request
from aiohttp.web_response import Response

from vims_code.app import ApplicationException, engine
from vims_code.auth.exceptions import WrongSession
from vims_code.auth.player_auth import PlayerAuthClass

from vims_code.models.team_game_auth import TeamGameAuth
from vims_code.urls.api import ActionRequest
from vims_code.utils.log import logger


async def parse_get_params(request: Request):
    params = dict(request.rel_url.query)
    return params


def load_contents(type_of_contents):
    """Фабричный метод, который определяет, какую функцию вызвать в зависимости от контекста.

    Args:
        type_of_contents(str): Тип контента

    Returns:
        function: Функция извлечения данных из запроса.
    """

    types = {
        "multipart/mixed": parse_multipart,
        "multipart/form-data": parse_multipart,
        "application/json": parse_json,
        "application/octet-stream": parse_octet_stream,
    }
    return types[type_of_contents]


@middleware
async def error_middleware(request, handler):
    """Обработчик ошибок.

    Args:
        request: Запрос.
        handler: Обработчик конкретного запроса.

    Returns:
        Response: Ответ.
    """
    try:

        if (
                hasattr(request.match_info._route, "status")
                and request.match_info._route.status == 404
        ):
            return json_response({"error": "not found"}, status=HTTPStatus.NOT_FOUND)

        response = await handler(request)

        if isinstance(response, dict) or isinstance(response, list):
            return json_response(response)
        else:
            return response
    except ApplicationException as ae:
        return json_response(
            {"res": None, "error": 1, "comments": ae.message}, status=ae.status
        )
    except HTTPException as ex:
        if ex.status != 404:
            raise
        message = ex.reason
    return json_response({"error": 1, "comments": message})


@middleware
async def main_middleware(request: Request, handler):
    request.player_id = None
    request.game_id = None
    request.team_id = None
    request.game_token = None
    async with engine.connect() as db_connection:
        try:
            token = (
                request.headers.get("token")
                if request.headers.get("token")
                else request.cookies.get("token")
            )
            game_token = request.headers.get('game-token')
            request.conn = db_connection
            if not hasattr(handler, "white_list") and not request.path.startswith(
                    "/docs"
            ):
                if token is None:
                    raise ApplicationException(43, "Сессия не передана", 403)
                player_id = await PlayerAuthClass(request.conn).identify_by_session(token)
                request.player_id = player_id
            if (hasattr(handler, "need_team_auth")):
                if game_token is None:
                    raise WrongSession("Сессия не передана")
                game_team_row = await TeamGameAuth(request.conn).identify_by_session(
                    token=game_token)
                if len(game_team_row) == 0:
                    raise WrongSession("Сессия неверна")
                request.game_id = game_team_row['game_id']
                request.team_id = game_team_row['team_id']
                request.game_token = game_token

            res = await handler(request)
            await db_connection.commit()
            return res
        except Exception as ex:
            raise ex
        finally:
            await db_connection.rollback()


@middleware
async def params_middleware(request: Request, handler):
    """Обработчик входящего запроса."""
    global white_list_urls
    request_path_set = set(request.path.split("/"))
    if request.path.startswith("/docs"):
        return await handler(request)
    content_dict = await load_contents(request.content_type)(request)
    action_request = ActionRequest(
        conn=request.conn,
        player_id=request.player_id,
        team_id=request.team_id,
        game_id=request.game_id,
        game_token=request.game_token
    )
    content_dict["action_request"] = action_request
    content_dict.update(dict(request.match_info))

    if "liveness" not in request_path_set and "readiness" not in request_path_set:
        logger.info(f"Action: {request.path}")
        logger.info(f"Params: {str(content_dict)}")

    for k in content_dict:
        content_dict[k] = content_dict[k] if content_dict[k] != "" else None
    result = await handler(**content_dict)
    if "liveness" not in request_path_set and "readiness" not in request_path_set:
        logger.info(f"res: {result}")
    if str(request.path).startswith("/server/download"):
        return web.FileResponse(result)
    else:
        return {"res": result, "error": 0, "comments": None}


async def parse_multipart(request):
    """Извлечение параметров из запроса.

    Args:
        request: запрос

    Returns:
        dict: Словарь с данными запроса
    """
    fields = await request.multipart()
    result_dict = {}
    async for field in fields:
        if field.filename:
            file_name = field.filename
            size = 0
            main_folder = os.environ.get("FILE_PATH", "_files")
            if not os.path.exists(f"{main_folder}"):
                os.makedirs(f"{main_folder}")
            file_path = f"{main_folder}/{file_name}"
            async with async_open(file_path, "wb+") as fd:
                while True:
                    chunk = await field.read_chunk()
                    if not chunk:
                        break
                    size += len(chunk)
                    await fd.write(chunk)
            result_dict[field.name] = file_path
        else:
            result_dict[field.name] = (await field.read()).decode()

    return result_dict


async def parse_json(request):
    """Извлечение параметров из запроса.

    Args:
        request: запрос

    Returns:
        dict: Словарь с данными запроса
    """
    return await request.json()


async def parse_octet_stream(request):
    """Извлечение параметров из запроса.

    Args:
        request: запрос

    Returns:
        dict: Словарь с данными запроса
    """

    if request.query:
        return {k: request.query[k] for k in request.query.keys()}

    return {key: request.match_info[key] for key in request.match_info.keys()}
