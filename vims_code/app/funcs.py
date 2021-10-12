from collections import namedtuple

from vims_code.models.api import DatabaseConnectionPool


def init_pool(config_name: str):
    from vims_code.app import config_parser
    return DatabaseConnectionPool(db_name=config_parser[config_name]['db_name'],  # 'auth'
                                  user=config_parser[config_name]['user'],  # 'mlapi',
                                  pwd=config_parser[config_name]['pwd'],  # 'mlapi',
                                  host=config_parser[config_name]['host'],  # 'goao-dev.ailab',
                                  min_number=int(config_parser[config_name]['min_number']),
                                  port=config_parser[config_name]['port'])  # 1)


TypeValue = namedtuple('TypeValue', ['type', 'value'])

CodeTypeValueClass = namedtuple('CodeTypeValueClass', ['code', 'type', 'value'])


class CodeTypeValueDict(dict):
    def __getitem__(self, item) -> TypeValue:
        return super().__getitem__(item)

    def __setitem__(self, key, value: TypeValue):
        super().__setitem__(key, value)


game_load_cache = {}
sql_cache = """
            select json_agg(to_json(gl.*)) table_json
             from e_code.game_list gl where gl.id = :game_id
            union all
            select json_agg(to_json(ll.*)) 
              from e_code.level_list ll 
            where ll.game_id = :game_id
              and (id = :level_id or cast(:level_id as bigint) is null)              
            union all
            select json_agg(to_json(lcl.*))
              from e_code.level_condition_list lcl
             where level_id in (select id from e_code.level_list ll where ll.game_id = :game_id)
               and (cast(:level_id as bigint) is null or level_id = :level_id)
            union all
            select json_agg(to_json(lrvl.*))
              from e_code.level_result_value_list lrvl
             where level_id in (select id from e_code.level_list ll where ll.game_id = :game_id)
               and (cast(:level_id as bigint) is null or level_id = :level_id)
            union all
            select json_agg(to_json(il.*))
              from e_code.info_list il
             where il.level_id in (select id from e_code.level_list ll where ll.game_id = :game_id)
               and (cast(:level_id as bigint) is null or il.level_id = :level_id)
            union all
            select json_agg(to_json(icl.*))
              from e_code.info_condition_list icl,
                   e_code.info_list il
             where 1=1
               and il.id = icl.info_id
               and (cast(:level_id as bigint) is null or il.level_id = :level_id)
               and il.level_id in (select id
                                     from e_code.level_list ll
                                    where ll.game_id = :game_id)
            union all
            select json_agg(to_json(cl.*))
              from e_code.code_list cl              
             where cl.level_id in (select id
                                     from e_code.level_list ll
                                    where ll.game_id = :game_id)
               and (cast(:level_id as bigint) is null or cl.level_id = :level_id)
            union all
            select json_agg(to_json(cpvl.*))
              from e_code.code_param_value_list cpvl,
                   e_code.code_list cl
             where 1=1
               and cl.id = cpvl.code_id
               and cl.level_id in (select id
                                     from e_code.level_list ll
                                    where ll.game_id = :game_id)
               and (cast(:level_id as bigint)  is null or cl.level_id = :level_id)
            union all
            select json_agg(to_json(crvl.*)) res
              from e_code.code_result_value_list crvl,
                   e_code.code_list cl
             where 1=1
               and cl.id = crvl.code_id
               and cl.level_id in (select id
                                     from e_code.level_list ll
                                    where ll.game_id = :game_id)
               and (cast(:level_id as bigint) is null or cl.level_id = :level_id)                                    
            union all
            
            select json_agg(to_json(ccl.*))
              from e_code.code_condition_list ccl,
                   e_code.code_list cl
             where 1=1
               and cl.id = ccl.code_id
               and cl.level_id in (select id
                                     from e_code.level_list ll
                                    where ll.game_id = :game_id)
               and (cast(:level_id as bigint) is null or cl.level_id = :level_id)                                    
            union all                                    
            select json_agg(to_json(t.*)) 
              from (
                select cvl.*, cl.level_id
                  from e_code.code_value_list cvl,
                       e_code.code_list cl
                 where cvl.code_id = cl.id
                   and (cast(:level_id as bigint) is null or cl.level_id = :level_id)
                   and cl.level_id in (select id
                                         from e_code.level_list ll
                                        where ll.game_id = :game_id)
                 ) t
            union all              
            select json_agg(to_json(t.*)) from (
                select * 
                 from e_code.team_game_code_list tgcl 
                 where tgcl.level_id in (select id 
                                           from e_code.level_list 
                                          where game_id = :game_id
                                            and (cast(:level_id as bigint) is null or id = :level_id)
                                          )
            ) t
            union all
            select json_agg(to_json(t.*)) from (
                select * 
                 from e_code.team_level_list tll 
                 where tll.level_id in (select id 
                                           from e_code.level_list 
                                          where game_id = :game_id
                                            and (cast(:level_id as bigint) is null or id = :level_id)
                                          )
            ) t
            union all
            select json_agg(to_json(t.*)) from (
                select tell.*, tl.level_id
                 from e_code.team_timer_event_list tell,
                      e_code.tick_list tl 
                 where 1=1
                   and tl.id = tell.tick_id 
                   and tl.level_id in (select id 
                                          from e_code.level_list                                                
                                          where game_id = :game_id
                                            and (cast(:level_id as bigint) is null or id = :level_id)
                                          )
                order by tell.id
            ) t
            
                              
                   
                                                
                                    
                                    
                                    """
cache_tables = ['game_list', 'level_list',
                'level_condition_list', 'level_result_value_list', 'info_list', 'info_condition_list',
                'code_list', 'code_param_value_list', 'code_result_value_list', 'code_condition_list',
                'code_value_list', 'team_game_code_list', 'team_level_list',
                'team_timer_event_list']
