-- migrate:up
alter table e_code.game_list
    alter column game_yaml drop not null;

-- migrate:down
alter table e_code.game_list
    alter column game_yaml set not null;