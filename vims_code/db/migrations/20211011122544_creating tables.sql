-- migrate:up
create table e_code.action_list
(
	id bigserial
		constraint action_list_pkey
			primary key,
	code_id bigint,
	level_id bigint,
	action_code varchar(80),
	action_type varchar(80),
	action_value varchar(2000)
);

alter table e_code.action_list owner to vims;

create index i_e_code_action_list_level_id
	on e_code.action_list (level_id);

create index i_e_code_action_list_code_id
	on e_code.action_list (code_id);

create table e_code.code_2_level
(
	id bigserial
		constraint code_2_level_pkey
			primary key,
	level_id bigint not null,
	code_id bigint not null
);

alter table e_code.code_2_level owner to vims;

create index i_e_code_code_2_level_level_id
	on e_code.code_2_level (level_id);

create table e_code.code_condition_list
(
	id bigserial
		constraint code_condition_list_pkey
			primary key,
	code_id bigint not null,
	condition_code varchar(80) not null,
	condition_type varchar(80) not null,
	condition_value varchar(2000) not null
);

alter table e_code.code_condition_list owner to vims;

create index i_e_code_code_condition_list_code_id
	on e_code.code_condition_list (code_id);

create table e_code.code_list
(
	id bigserial
		constraint code_list_pkey
			primary key,
	caption varchar(400) not null,
	code_type varchar(80) not null,
	code_tags varchar(1000),
	code_values_info text,
	code_inner_id varchar(80),
	level_id bigint
);

alter table e_code.code_list owner to vims;

create index i_e_code_code_list_level_id
	on e_code.code_list (level_id);

create table e_code.code_param_value_list
(
	id bigserial
		constraint code_param_value_list_pkey
			primary key,
	code_id bigint not null,
	param_code varchar(80) not null,
	param_type varchar(80) not null,
	param_value varchar(800) not null
);

alter table e_code.code_param_value_list owner to vims;

create index i_e_code_code_param_value_list_code_id
	on e_code.code_param_value_list (code_id);

create table e_code.code_result_value_list
(
	id bigserial
		constraint code_result_value_list_pkey
			primary key,
	code_id bigint not null,
	result_code varchar(80) not null,
	result_type varchar(80) not null,
	result_value varchar(2000) not null
);

alter table e_code.code_result_value_list owner to vims;

create index i_e_code_code_result_value_list_code_id
	on e_code.code_result_value_list (code_id);

create table e_code.code_value_list
(
	id bigserial
		constraint code_value_list_pkey
			primary key,
	code_id bigint not null,
	value_type varchar(80) not null,
	code_value varchar(80) not null
);

alter table e_code.code_value_list owner to vims;

create index i_e_code_code_value_list_code_id
	on e_code.code_value_list (code_id);

create table e_code.game_author_list
(
	id bigserial
		constraint game_author_list_pkey
			primary key,
	game_id bigint not null,
	author_id bigint not null,
	author_role varchar(80) not null
);

alter table e_code.game_author_list owner to vims;

create index i_e_code_game_author_list_game_id
	on e_code.game_author_list (game_id);

create index i_e_code_game_author_list_author_id
	on e_code.game_author_list (author_id);

create table e_code.game_list
(
	id bigserial
		constraint game_list_pkey
			primary key,
	game_state varchar(80) not null,
	game_type varchar(80),
	caption varchar(400) not null,
	game_yaml text not null,
	creation_date timestamp not null
);

alter table e_code.game_list owner to vims;

create table e_code.game_team_info
(
	id bigserial
		constraint game_team_info_pkey
			primary key,
	game_id bigint not null,
	team_id bigint not null,
	level_script text not null,
	accepted integer not null
);

alter table e_code.game_team_info owner to vims;

create index i_gti_game_team
	on e_code.game_team_info (game_id, team_id);

create index i_e_code_game_team_info_game_id
	on e_code.game_team_info (game_id);

create index i_e_code_game_team_info_team_id
	on e_code.game_team_info (team_id);

create table e_code.game_team_scores
(
	id bigserial
		constraint game_team_scores_pkey
			primary key,
	game_id bigint not null,
	team_id bigint not null,
	level_id bigint,
	result_code varchar(80) not null,
	result_value varchar(2000),
	source_code_id bigint,
	source_level_id bigint,
	source_tick_id bigint,
	insert_date timestamp default CURRENT_TIMESTAMP
);

alter table e_code.game_team_scores owner to vims;

create index i_gts_game_team_level
	on e_code.game_team_scores (game_id, team_id, level_id);

create table e_code.info_condition_list
(
	id bigserial
		constraint info_condition_list_pkey
			primary key,
	info_id bigint not null,
	condition_code varchar(80) not null,
	condition_type varchar(80) not null,
	condition_value varchar(2000) not null
);

alter table e_code.info_condition_list owner to vims;

create index i_e_code_info_condition_list_info_id
	on e_code.info_condition_list (info_id);

create table e_code.info_list
(
	id bigserial
		constraint info_list_pkey
			primary key,
	info_caption varchar(400),
	info_text text,
	level_id bigint,
	inner_id varchar(80),
	condition_script text
);

alter table e_code.info_list owner to vims;

create index i_il_level_code
	on e_code.info_list (level_id, inner_id);

create table e_code.level_condition_list
(
	id bigserial
		constraint level_condition_list_pkey
			primary key,
	level_id bigint not null,
	condition_code varchar(80) not null,
	condition_type varchar(80) not null,
	condition_value varchar(2000) not null,
	is_fail integer
);

alter table e_code.level_condition_list owner to vims;

create index i_e_code_level_condition_list_level_id
	on e_code.level_condition_list (level_id);

create table e_code.level_list
(
	id bigserial
		constraint level_list_pkey
			primary key,
	caption varchar(400),
	game_id bigint not null,
	level_type varchar(80),
	inner_id varchar(80),
	condition_script text,
	failed_condition_script text
);

alter table e_code.level_list owner to vims;

create index i_ll_game_inner
	on e_code.level_list (game_id, inner_id);

create table e_code.level_result_value_list
(
	id bigserial
		constraint level_result_value_list_pkey
			primary key,
	level_id bigint not null,
	result_code varchar(80) not null,
	result_type varchar(80) not null,
	result_value varchar(2000) not null,
	is_fail integer
);

alter table e_code.level_result_value_list owner to vims;

create index i_e_code_level_result_value_list_level_id
	on e_code.level_result_value_list (level_id);

create table e_code.player_auth
(
	id bigserial
		constraint player_auth_pkey
			primary key,
	session_id varchar(80) not null,
	player_id bigint not null,
	date_start timestamp not null,
	date_expire timestamp not null,
	num_of_devices integer
);

alter table e_code.player_auth owner to vims;

create index i_e_code_player_auth_session_id
	on e_code.player_auth (session_id);

create table e_code.player_game_2_team
(
	id bigserial
		constraint player_game_2_team_pkey
			primary key,
	player_id bigint not null,
	token varchar(80) not null,
	team_id bigint not null,
	game_id bigint not null,
	is_active integer
);

alter table e_code.player_game_2_team owner to vims;

create index i_e_code_player_game_2_team_token
	on e_code.player_game_2_team (token);

create table e_code.player_list
(
	id bigserial
		constraint player_list_pkey
			primary key,
	player_login varchar(20) not null,
	player_pwd varchar(80),
	player_salt varchar(20),
	player_state varchar(20),
	email varchar(200)
);

alter table e_code.player_list owner to vims;

create index i_e_code_player_list_player_login
	on e_code.player_list (player_login);

create table e_code.team
(
	id bigserial
		constraint team_pkey
			primary key,
	caption varchar(800) not null,
	creation_date timestamp default CURRENT_TIMESTAMP
);

alter table e_code.team owner to vims;

create table e_code.team_game_auth
(
	id bigserial
		constraint team_game_auth_pkey
			primary key,
	token varchar(80) not null,
	team_id bigint not null,
	game_id bigint not null,
	is_active integer
);

alter table e_code.team_game_auth owner to vims;

create index i_e_code_team_game_auth_token
	on e_code.team_game_auth (token);

create table e_code.team_game_code_list
(
	id bigserial
		constraint team_game_code_list_pkey
			primary key,
	team_id bigint not null,
	code_id bigint,
	level_id bigint,
	code_value varchar(800) not null,
	insert_date timestamp default CURRENT_TIMESTAMP,
	tick_step bigint
);

alter table e_code.team_game_code_list owner to vims;

create index i_e_code_team_game_code_list_team_id
	on e_code.team_game_code_list (team_id);

create table e_code.team_info_list
(
	id bigserial
		constraint team_info_list_pkey
			primary key,
	team_id bigint not null,
	info_id bigint,
	info_status varchar(80)
);

alter table e_code.team_info_list owner to vims;

create index i_e_code_team_info_list_team_id
	on e_code.team_info_list (team_id);

create table e_code.team_level_list
(
	id bigserial
		constraint team_level_list_pkey
			primary key,
	team_id bigint not null,
	level_id bigint,
	level_status varchar(80),
	done integer
);

alter table e_code.team_level_list owner to vims;

create index i_e_code_team_level_list_team_id
	on e_code.team_level_list (team_id);

create table e_code.team_player_role_list
(
	id bigserial
		constraint team_player_role_list_pkey
			primary key,
	team_id bigint not null,
	player_id bigint not null,
	player_role varchar(80) not null
);

alter table e_code.team_player_role_list owner to vims;

create index i_tprl_team_player
	on e_code.team_player_role_list (team_id, player_id);

create table e_code.team_timer_event_list
(
	id bigserial
		constraint team_timer_event_list_pkey
			primary key,
	team_id bigint not null,
	tick_id bigint not null,
	event varchar(80) not null,
	event_date timestamp default CURRENT_TIMESTAMP
);

alter table e_code.team_timer_event_list owner to vims;

create index i_e_code_team_timer_event_list_tick_id
	on e_code.team_timer_event_list (tick_id);

create index i_e_code_team_timer_event_list_team_id
	on e_code.team_timer_event_list (team_id);

create table e_code.tick_list
(
	id bigserial
		constraint tick_list_pkey
			primary key,
	tick_type varchar(80),
	level_id bigint not null,
	step integer,
	starts_from bigint,
	finish_at bigint,
	tick_info text
);

alter table e_code.tick_list owner to vims;

create index i_e_code_tick_list_level_id
	on e_code.tick_list (level_id);

create table e_code.tick_param_value_list
(
	id bigserial
		constraint tick_param_value_list_pkey
			primary key,
	tick_id bigint not null,
	param_code varchar(80) not null,
	param_type varchar(80) not null,
	param_value varchar(2000) not null
);

alter table e_code.tick_param_value_list owner to vims;

create index i_e_code_tick_param_value_list_tick_id
	on e_code.tick_param_value_list (tick_id);

create table e_code.tick_step
(
	id bigserial
		constraint tick_step_pkey
			primary key,
	team_id bigint not null,
	tick_id bigint not null,
	num_of_steps bigint not null
);

alter table e_code.tick_step owner to vims;

create index i_e_code_tick_step_team_id
	on e_code.tick_step (team_id);

create table e_code.variable_list
(
	id bigserial
		constraint variable_list_pkey
			primary key,
	game_id bigint not null,
	variable_code varchar(80) not null,
	variable_type varchar(80) not null,
	comments text
);

alter table e_code.variable_list owner to vims;

create index i_e_code_variable_list_game_id
	on e_code.variable_list (game_id);



-- migrate:down
drop table e_code.game_team_scores;
drop table e_code.player_game_2_team;
drop table e_code.player_list;
drop table e_code.game_author_list;
drop table e_code.info_list;
drop table e_code.variable_list;
drop table e_code.level_list;
drop table e_code.level_condition_list;drop table e_code.tick_param_value_list;
drop table e_code.game_list;
drop table e_code.game_team_info;
drop table e_code.level_result_value_list;
drop table e_code.team_level_list;
drop table e_code.player_auth;
drop table e_code.team_player_role_list;
drop table e_code.team_timer_event_list;
drop table e_code.tick_step;
drop table e_code.tick_list;
drop table e_code.team_info_list;
drop table e_code.info_condition_list;
drop table e_code.team_game_code_list;
drop table e_code.team;
drop table e_code.code_param_value_list;
drop table e_code.team_game_auth;
drop table e_code.code_value_list;
drop table e_code.code_result_value_list;
drop table e_code.code_list;
drop table e_code.code_condition_list;
drop table e_code.code_2_level;
drop table e_code.action_list;

