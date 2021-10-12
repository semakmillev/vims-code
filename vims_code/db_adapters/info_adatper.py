from vims_code.models.api import DatabaseConnection
from vims_code.models.info_condition_list import InfoConditionList
from vims_code.models.info_list import InfoList
from db_adapters.code_adapter import CodeAdapter


class InfoAdapter(object):
    def __init__(self, conn: DatabaseConnection):
        self.conn = conn
        self.il = InfoList(conn)
        self.icl = InfoConditionList(conn)
        self.ca = CodeAdapter(conn)

    def delete(self, info_id):
        condition_list = self.icl.select(id=info_id)
        for condition in condition_list:
            if condition == 'BY_REQUEST':
                self.ca.delete_code(self.ca.get_code_by_inner_id(condition['condition_value'].split(':')[0]))
            self.icl.delete(condition['id'])
        self.il.delete(id=info_id)
