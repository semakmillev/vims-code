-- migrate:up
alter table e_code.info_list
    add info_type varchar(20) default 'SIMPLE';

alter table e_code.info_list
    add level_link varchar(200) default null;

-- migrate:down
alter table e_code.info_list
    drop column info_type;

alter table e_code.info_list
    drop column level_link;

