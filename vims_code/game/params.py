class Condition(object):
    def __init__(self, condition_code: str, condition_type, condition_value, is_fail=0):
        self.condition_code = condition_code
        self.condition_type = condition_type
        self.condition_value = condition_value
        self.is_fail = is_fail

    def json_info(self):
        return {"code": self.condition_code, "type": self.condition_type, "value": self.condition_value}


class Result(object):
    def __init__(self, result_code, result_type, result_value):
        self.result_code: str = result_code
        self.result_type = result_type
        if result_type in ('SIMPLE', 'PENALTY', 'BONUS', 'BLOCK'):
            self.result_value = int(result_value if result_value != '' else 0)
        if result_type == '@':
            self.result_value = result_value

    def json_info(self):
        res = {}
        res['code'] = self.result_code
        res['type'] = self.result_type
        res['value'] = self.result_value
        return res

    def init_result_in_scores(self):
        return 0


    '''
    def add_result(self, res):
        self.result_value += int(res)
        
        elif self.result_value == 'CONCAT_TEXT':
            self.result_value += str(res)
    '''


class ConditionDict(dict):
    def __getitem__(self, item: str) -> Condition:
        return super().__getitem__(item)

    def __setitem__(self, key: str, value: Condition):
        super().__setitem__(key, value)
