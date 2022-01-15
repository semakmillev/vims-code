from sqlalchemy import (
    JSON,
    TIMESTAMP,
    BigInteger,
    Column,
    MetaData,
    SmallInteger,
    String,
    Table,
    Text,
    DateTime,
    Integer,
    func,
    Index,
    text,
)

metadata = MetaData(schema="e_code")

TABLE_CODE = String(80)
TABLE_NAME = String(400)

t_action_list = Table(
    "action_list",
    metadata,
    Column("id", BigInteger, nullable=False, autoincrement=True, primary_key=True),
    Column("code_id", BigInteger, nullable=True, index=True),
    Column("level_id", BigInteger, nullable=True, index=True),
    Column("action_code", TABLE_CODE, nullable=True),
    Column("action_type", TABLE_CODE, nullable=True),
    Column("action_value", String(2000), nullable=True),
)


t_code_condition_list = Table(
    "code_condition_list",
    metadata,
    Column("id", BigInteger, nullable=False, autoincrement=True, primary_key=True),
    Column("code_id", BigInteger, nullable=False, index=True),
    Column("condition_code", TABLE_CODE, nullable=False),
    Column("condition_type", TABLE_CODE, nullable=False),
    Column("condition_value", String(2000), nullable=False),
)

Index(
    "ui_e_code_code_condition_list_code_id",
    t_code_condition_list.c.code_id,
    t_code_condition_list.c.condition_code,
)

t_code_list = Table(
    "code_list",
    metadata,
    Column("id", BigInteger, nullable=False, autoincrement=True, primary_key=True),
    Column("caption", TABLE_NAME, nullable=False),
    Column("code_type", TABLE_CODE, nullable=False),
    Column("code_tags", String(1000), nullable=True),
    Column("code_values_info", Text, nullable=True),
    Column("code_inner_id", TABLE_CODE, nullable=True),
    Column("level_id", BigInteger, nullable=True, index=True),
)

t_code_param_value_list = Table(
    "code_param_value_list",
    metadata,
    Column("id", BigInteger, nullable=False, autoincrement=True, primary_key=True),
    Column("code_id", BigInteger, nullable=False, index=True),
    Column("param_code", TABLE_CODE, nullable=False),
    Column("param_type", TABLE_CODE, nullable=False),
    Column("param_value", String(800), nullable=False),
)

t_code_result_value_list = Table(
    "code_result_value_list",
    metadata,
    Column("id", BigInteger, nullable=False, autoincrement=True, primary_key=True),
    Column("code_id", BigInteger, nullable=False, index=True),
    Column("result_code", TABLE_CODE, nullable=False),
    Column("result_type", TABLE_CODE, nullable=False),
    Column("result_value", String(2000), nullable=False),
)

Index(
    "ui_e_code_code_result_value_list_code_id",
    t_code_result_value_list.c.code_id,
    t_code_result_value_list.c.result_code,
)

t_game_author_list = Table(
    "game_author_list",
    metadata,
    Column("id", BigInteger, nullable=False, autoincrement=True, primary_key=True),
    Column("game_id", BigInteger, nullable=False, index=True),
    Column("author_id", BigInteger, nullable=False, index=True),
    Column("author_role", TABLE_CODE, nullable=False),
)

t_game_list = Table(
    "game_list",
    metadata,
    Column("id", BigInteger, nullable=False, autoincrement=True, primary_key=True),
    Column("game_state", TABLE_CODE, nullable=False),
    Column("game_type", TABLE_CODE, nullable=True),
    Column("caption", TABLE_NAME, nullable=False),
    Column("game_yaml", Text, nullable=False),
    Column("creation_date", DateTime, nullable=False),
)
t_game_team_info = Table(
    "game_team_info",
    metadata,
    Column("id", BigInteger, nullable=False, autoincrement=True, primary_key=True),
    Column("game_id", BigInteger, nullable=False, index=True),
    Column("team_id", BigInteger, nullable=False, index=True),
    Column("level_script", Text, nullable=False, index=False),
    Column("accepted", Integer, nullable=False, default=0),
)

Index("i_gti_game_team", t_game_team_info.c.game_id, t_game_team_info.c.team_id)

t_game_team_scores = Table(
    "game_team_scores",
    metadata,
    Column("id", BigInteger, nullable=False, autoincrement=True, primary_key=True),
    Column("game_id", BigInteger, nullable=False),
    Column("team_id", BigInteger, nullable=False),
    Column("level_id", BigInteger, nullable=True),
    Column("result_code", TABLE_CODE, nullable=False),
    Column("result_value", String(2000), nullable=True),
    Column("source_code_id", BigInteger, nullable=True),
    Column("source_level_id", BigInteger, nullable=True),
    Column("source_tick_id", BigInteger, nullable=True),
    Column("insert_date", DateTime, server_default=text("CURRENT_TIMESTAMP")),
)

Index(
    "i_gts_game_team_level",
    t_game_team_scores.c.game_id,
    t_game_team_scores.c.team_id,
    t_game_team_scores.c.level_id,
)

t_info_condition_list = Table(
    "info_condition_list",
    metadata,
    Column("id", BigInteger, nullable=False, autoincrement=True, primary_key=True),
    Column("info_id", BigInteger, nullable=False),
    Column("condition_code", TABLE_CODE, nullable=False),
    Column("condition_type", TABLE_CODE, nullable=False),
    Column("condition_value", String(2000), nullable=False),
)
Index("ui_e_code_info_condition_list_info_id",
      t_info_condition_list.c.info_id,
      t_info_condition_list.c.condition_code, unique=True)

t_info_list = Table(
    "info_list",
    metadata,
    Column("id", BigInteger, nullable=False, autoincrement=True, primary_key=True),
    Column("info_caption", TABLE_NAME, nullable=True),
    Column("info_text", Text, nullable=True),
    Column("level_id", BigInteger, nullable=True),
    Column("inner_id", TABLE_CODE, nullable=True),
    Column("condition_script", Text, nullable=True),
    Column("info_type", String(200), nullable=True, default='SIMPLE'),
    Column("level_link", String(200), nullable=True),
)

Index(
    "i_il_level_code",
    t_info_list.c.level_id,
    t_info_list.c.inner_id,
)

t_level_condition_list = Table(
    "level_condition_list",
    metadata,
    Column("id", BigInteger, nullable=False, autoincrement=True, primary_key=True),
    Column("level_id", BigInteger, nullable=False, index=True),
    Column("condition_code", TABLE_CODE, nullable=False),
    Column("condition_type", TABLE_CODE, nullable=False),
    Column("condition_value", String(2000), nullable=False),
    Column("is_fail", Integer, default=0),
)

t_level_list = Table(
    "level_list",
    metadata,
    Column("id", BigInteger, nullable=False, autoincrement=True, primary_key=True),
    Column("caption", TABLE_NAME, nullable=True),
    Column("game_id", BigInteger, nullable=False),
    Column("level_type", TABLE_CODE, nullable=True),
    Column("inner_id", TABLE_CODE, nullable=True),
    Column("condition_script", Text, nullable=True),
    Column("failed_condition_script", Text, nullable=True),
)

Index(
    "i_ll_game_inner",
    t_level_list.c.game_id,
    t_level_list.c.inner_id,
)

t_level_result_value_list = Table(
    "level_result_value_list",
    metadata,
    Column("id", BigInteger, nullable=False, autoincrement=True, primary_key=True),
    Column("level_id", BigInteger, nullable=False, index=True),
    Column("result_code", TABLE_CODE, nullable=False),
    Column("result_type", TABLE_CODE, nullable=False),
    Column("result_value", String(2000), nullable=False),
    Column("is_fail", Integer, default=0),
)

t_player_auth = Table(
    "player_auth",
    metadata,
    Column("id", BigInteger, nullable=False, autoincrement=True, primary_key=True),
    Column("session_id", TABLE_CODE, nullable=False, index=True),
    Column("player_id", BigInteger, nullable=False),
    Column("date_start", DateTime, nullable=False),
    Column("date_expire", DateTime, nullable=True),
    Column("num_of_devices", Integer, default=1),
)

t_player_game_2_team = Table(
    "player_game_2_team",
    metadata,
    Column("id", BigInteger, nullable=False, autoincrement=True, primary_key=True),
    Column("player_id", BigInteger, nullable=False),
    Column("token", TABLE_CODE, nullable=False, index=True),
    Column("team_id", BigInteger, nullable=False),
    Column("game_id", BigInteger, nullable=False),
    Column("is_active", Integer, default=1),
)

t_player_list = Table(
    "player_list",
    metadata,
    Column("id", BigInteger, nullable=False, autoincrement=True, primary_key=True),
    Column("player_login", String(20), nullable=False, index=True),
    Column("player_type", String(80), nullable=False, default='HUMAN'),
    Column("player_pwd", String(80), nullable=True),
    Column("player_salt", String(20), nullable=True),
    Column("player_state", String(20), nullable=True),
    Column("email", String(200), nullable=True),
)

t_team = Table(
    "team",
    metadata,
    Column("id", BigInteger, nullable=False, autoincrement=True, primary_key=True),
    Column("caption", String(800), nullable=False),
    Column("creation_date", DateTime, server_default=text("CURRENT_TIMESTAMP")),
)

t_team_game_auth = Table(
    "team_game_auth",
    metadata,
    Column("id", BigInteger, nullable=False, autoincrement=True, primary_key=True),
    Column("token", TABLE_CODE, nullable=False, index=True),
    Column("team_id", BigInteger, nullable=False),
    Column("game_id", BigInteger, nullable=False),
    Column("is_active", Integer, default=1),
)

t_team_game_code_list = Table(
    "team_game_code_list",
    metadata,
    Column("id", BigInteger, nullable=False, autoincrement=True, primary_key=True),
    Column("team_id", BigInteger, nullable=False, index=True),
    Column("code_id", BigInteger, nullable=True),
    Column("level_id", BigInteger, nullable=True),
    Column("code_value", String(800), nullable=False),
    Column("insert_date", DateTime, server_default=text("CURRENT_TIMESTAMP")),
    Column("tick_step", BigInteger, default=0),
)

t_team_info_list = Table(
    "team_info_list",
    metadata,
    Column("id", BigInteger, nullable=False, autoincrement=True, primary_key=True),
    Column("team_id", BigInteger, nullable=False, index=True),
    Column("info_id", BigInteger, nullable=True),
    Column("info_status", TABLE_CODE, nullable=True),
)
t_team_level_list = Table(
    "team_level_list",
    metadata,
    Column("id", BigInteger, nullable=False, autoincrement=True, primary_key=True),
    Column("team_id", BigInteger, nullable=False, index=True),
    Column("level_id", BigInteger, nullable=True),
    Column("level_status", TABLE_CODE, nullable=True),
    Column("done", Integer, default=0),
)

t_team_player_role_list = Table(
    "team_player_role_list",
    metadata,
    Column("id", BigInteger, nullable=False, autoincrement=True, primary_key=True),
    Column("team_id", BigInteger, nullable=False),
    Column("player_id", BigInteger, nullable=False),
    Column("player_role", TABLE_CODE, nullable=False),
)

Index(
    "i_tprl_team_player",
    t_team_player_role_list.c.team_id,
    t_team_player_role_list.c.player_id,
)

t_team_timer_event_list = Table(
    "team_timer_event_list",
    metadata,
    Column("id", BigInteger, nullable=False, autoincrement=True, primary_key=True),
    Column("team_id", BigInteger, nullable=False, index=True),
    Column("tick_id", BigInteger, nullable=False, index=True),
    Column("event", TABLE_CODE, nullable=False),
    Column("event_date", DateTime, server_default=text("CURRENT_TIMESTAMP")),
)

t_tick_list = Table(
    "tick_list",
    metadata,
    Column("id", BigInteger, nullable=False, autoincrement=True, primary_key=True),
    Column("tick_type", TABLE_CODE, default="LEVEL"),
    Column("level_id", BigInteger, nullable=False, index=True),
    Column("step", Integer, nullable=True),
    Column("starts_from", BigInteger, default=0),
    Column("finish_at", BigInteger, default=0),
    Column("tick_info", Text, nullable=True),
)

t_tick_param_value_list = Table(
    "tick_param_value_list",
    metadata,
    Column("id", BigInteger, nullable=False, autoincrement=True, primary_key=True),
    Column("tick_id", BigInteger, nullable=False, index=True),
    Column("param_code", TABLE_CODE, nullable=False),
    Column("param_type", TABLE_CODE, nullable=False),
    Column("param_value", String(2000), nullable=False),
)

t_tick_step = Table(
    "tick_step",
    metadata,
    Column("id", BigInteger, nullable=False, autoincrement=True, primary_key=True),
    Column("team_id", BigInteger, nullable=False, index=True),
    Column("tick_id", BigInteger, nullable=False),
    Column("num_of_steps", BigInteger, nullable=False)
)

t_variable_list = Table(
    "variable_list",
    metadata,
    Column("id", BigInteger, nullable=False, autoincrement=True, primary_key=True),
    Column("game_id", BigInteger, nullable=False, index=True),
    Column("variable_code", TABLE_CODE, nullable=False),
    Column("variable_type", TABLE_CODE, nullable=False),
    Column("comments", Text, nullable=True),
)
