-- migrate:up
drop table code_value_list;

-- migrate:down
create table code_value_list
(
    id         bigserial
        constraint code_value_list_pkey
            primary key,
    code_id    bigint      not null,
    value_type varchar(80) not null,
    code_value varchar(80) not null
);

alter table code_value_list
    owner to vims;

create index i_e_code_code_value_list_code_id
    on code_value_list (code_id);


