from vims_code.models.code_result_value_list import CodeResultValueList
from vims_code.models.game_team_results import GameTeamResults
from vims_code.models.level_condition_list import LevelConditionList
from vims_code.models.team_game_code_list import TeamGameCodeList
from vims_code.game.codes import Code
from vims_code.game.levels import Level, LevelFinishedException
from vims_code.game.scores import Result
from vims_code.game.team import Team




def complete_code(team: Team, code: Code):
    """ No checks! """

    cl = TeamGameCodeList(team.conn)
    gtr = GameTeamResults(team.conn)

    for code_result_code in code.results:
        code_result = code.results[code_result_code]
        if code_result_code.startswith("_"):
            team.team_scores.add_game_score(result=Result(code_result_code, code_result.type, code_result.value))
            level_id = None
        else:
            level_id = code.level_id
            team.team_scores.add_level_score(level_id,
                                             result=Result(code_result_code, code_result.type, code_result.value))
        gtr.set(id=None,
                game_id=team.game_id,
                level_id=level_id,
                result_code=code_result_code,
                result_value=code_result.value,
                source_code_id=code.code_id,
                source_level_id=code.level_id,
                team_id=team.team_id
                )
    cl.set(id=None, team_id=team.team_id, code_id=code.code_id)
