import datetime

from sqlalchemy import text

from vims_code.db.schema import t_player_auth
from vims_code.models.base import SqlTable


class PlayerAuth(SqlTable):
    table = t_player_auth

    async def identify_by_session(self, session_id: str):
        sql = """select pa.id, pa.player_id
                   from e_code.player_auth pa 
                  where session_id = :session_id
                    and date_expire is null"""
        try:
            return (await self.call_select(text(sql), dict(session_id=session_id)))[0]
        except IndexError:
            return None
