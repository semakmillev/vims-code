-- migrate:up
drop table code_2_level;

-- migrate:down

create table code_2_level
(
    id       bigserial
        constraint code_2_level_pkey
            primary key,
    level_id bigint not null,
    code_id  bigint not null
);

alter table code_2_level
    owner to vims;

create index i_e_code_code_2_level_level_id
    on code_2_level (level_id);
