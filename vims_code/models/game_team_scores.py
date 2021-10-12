from sqlalchemy import text

from vims_code.db.schema import t_game_team_scores
from vims_code.models.api import DatabaseTable, Field, DbTypes
from vims_code.models.base import SqlTable


class GameTeamScores(SqlTable):
    table = t_game_team_scores

    async def select_current_values(self, game_id, team_id, level_id):
        sql = """select * 
                   from e_code.game_team_scores gtr
                  where gtr.game_id =  %(game_id)s
                    and (gtr.level_id = %(level_id)s or gtr.level_id is null)
                    and gtr.team_id = %(team_id)s
                  """
        rows = (
            await self.conn.execute(
                text(sql), {"game_id": game_id, "level_id": level_id, "team_id": team_id}
            )
        ).fetchall()
        return [dict(r) for r in rows]

    async def add_tick_number(
        self,
        game_id: int = None,
        team_id: int = None,
        level_id: int = None,
        result_code: str = None,
        result_value: str = None,
    ):
        sql = """update e_code.game_team_scores
                    set result_value = result_value + :result_value
                where game_id = :game_id
                  and team_id = :team_id
                  and (level_id = :level_id or (level_id is null and :level_id is null))
                  and result_code = :result_code
        """
        await self.conn.execute(
            text(sql),
            dict(
                game_id=game_id,
                team_id=team_id,
                level_id=level_id,
                result_code=result_code,
                result_value=result_value,
            ),
        )

    def finish_level(self, level_id: int, game_id: int, team_id: int, is_fail: int = 0):
        sql = """
        insert into e_code.game_team_scores (game_id,
                                             team_id,
                                             level_id,
                                             result_code,
                                             result_value,
                                             source_code_id,
                                             source_level_id, 
                                             source_tick_id)
          select %(game_id)s, %(team_id)s, null, lrvl.result_code, lrvl.result_value, null, lrvl.level_id, null
            from e_code.level_result_value_list lrvl
           where lrvl.level_id = %(level_id)s
             and lrvl.is_fail = %(is_fail)s                       
        """
        self.conn.call_query(
            sql,
            dict(game_id=game_id, team_id=team_id, level_id=level_id, is_fail=is_fail),
        )

    def set(
        self,
        id: int = None,
        game_id: int = None,
        team_id: int = None,
        level_id: int = None,
        result_code: str = None,
        result_value: str = None,
        source_code_id: int = None,
        source_level_id: int = None,
        source_tick_id: int = None,
    ):
        return super()._set(
            id=id,
            game_id=game_id,
            team_id=team_id,
            level_id=level_id,
            result_code=result_code,
            result_value=result_value,
            source_code_id=source_code_id,
            source_level_id=source_level_id,
            source_tick_id=source_tick_id,
        )

    def delete(self, id: int):
        super()._delete("id", id)

    def delete_by_team(self, team_id: int):
        super()._delete("team_id", team_id)
