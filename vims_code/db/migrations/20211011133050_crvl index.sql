-- migrate:up
drop index e_code.i_e_code_code_result_value_list_code_id;

create unique index ui_e_code_code_result_value_list_code_id
	on e_code.code_result_value_list (code_id, result_code);


drop index e_code.i_e_code_code_condition_list_code_id;

create unique index ui_e_code_code_condition_list_code_id
	on e_code.code_condition_list (code_id, condition_code);


-- migrate:down

drop index e_code.ui_e_code_code_result_value_list_code_id;

create unique index i_e_code_code_result_value_list_code_id
	on e_code.code_result_value_list (code_id);

drop index e_code.ui_e_code_code_condition_list_code_id;

create unique index i_e_code_code_condition_list_code_id
	on e_code.code_result_value_list (code_id);