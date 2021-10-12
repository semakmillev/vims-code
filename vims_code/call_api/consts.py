import datetime
from typing import List


class API_TYPES:
    str_type = {"type": "str"}
    num_type = {"type": "num"}
    datetime_type = {"type": "datetime"}


_API_TYPE_DICT = {
    "int": API_TYPES.num_type,
    "str": API_TYPES.str_type,
    "datetime": API_TYPES.datetime_type
}
API_TYPE_DICT = {
    str(dict): {"type": "object"},
    str(int): {"type": "num"},
    str(str): {"type": "str"},
    str(datetime.datetime): {"type": "datetime"},
    str(List[int]): {"type": "array", "items": {"type": "num"}}
}
