from vims_code.models.api import DatabaseConnection
from vims_code.models.game_team_scores import GameTeamScores
from vims_code.models.level_list import LevelList
from vims_code.models.team_game_code_list import TeamGameCodeList
from vims_code.models.team_level_list import TeamLevelList
from vims_code.models.tick_step import TickStep


def clear_game(conn: DatabaseConnection, team_id: int, game_id: int):
    ts = TickStep(conn)
    ts.delete_by_team(team_id)
    tgcl = TeamGameCodeList(conn)
    tgcl.delete_by_team(team_id=team_id)
    gts = GameTeamScores(conn)
    gts.delete_by_team(team_id=team_id)
    tll = TeamLevelList(conn)
    ll = LevelList(conn)
    level_rows = ll.select(game_id=game_id)
    for level_row in level_rows:
        tll.set_level_status(team_id, level_row['id'], 'PLANNED', 0)
