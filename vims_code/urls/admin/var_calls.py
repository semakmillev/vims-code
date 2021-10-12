

from vims_code.models.variable_list import VariableList
from vims_code.urls.admin.api import admin_routes, check_author
from vims_code.urls.api import ActionRequest


@admin_routes.get("/server/api/admin.variable_list")
async def get_variable_list(game_id: int, action_request: ActionRequest = None) -> {}:
    # level_id = int(level_id)
    await check_author(action_request.conn, action_request.player_id, game_id=game_id)
    res = VariableList(action_request.conn).select_game_vars(game_id=game_id)
    return res


@admin_routes.post("/server/api/admin.set_variable_list")
async def set_variable_list(var_list, game_id, action_request: ActionRequest = None) -> {}:
    # level_id = int(level_id)
    await check_author(action_request.conn, action_request.player_id, game_id=game_id)
    vl = VariableList(action_request.conn)
    for v in var_list:
        if v.get('game_id') is not None:
            await vl.set(**v)


@admin_routes.post("/server/api/admin.delete_variable")
def delete_variable(var_id, var_code, game_id):
    pass