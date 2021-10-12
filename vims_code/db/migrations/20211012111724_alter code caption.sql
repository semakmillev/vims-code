-- migrate:up
alter table e_code.code_list
    alter column caption drop not null;

-- migrate:down
alter table e_code.code_list
    alter column caption set not null;