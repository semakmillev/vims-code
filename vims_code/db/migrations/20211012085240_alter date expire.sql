-- migrate:up
alter table e_code.player_auth
    alter column date_expire drop not null;

-- migrate:down
alter table e_code.player_auth
    alter column date_expire set not null;