-- migrate:up
drop index e_code.i_e_code_info_condition_list_info_id;

create unique index ui_e_code_info_condition_list_info_id
	on e_code.info_condition_list (info_id, condition_code);



-- migrate:down

drop index e_code.ui_e_code_info_condition_list_info_id;

create unique index i_e_code_info_condition_list_info_id
	on e_code.info_condition_list (info_id);
