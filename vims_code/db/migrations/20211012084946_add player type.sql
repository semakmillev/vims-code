-- migrate:up
alter table e_code.player_list
    add column player_type varchar(80);

-- migrate:down
alter table e_code.player_list
    drop column player_type;
