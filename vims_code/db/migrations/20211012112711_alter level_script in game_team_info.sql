-- migrate:up
alter table e_code.game_team_info
    alter column level_script drop not null;

-- migrate:down
alter table e_code.game_team_info
    alter column level_script set not null;