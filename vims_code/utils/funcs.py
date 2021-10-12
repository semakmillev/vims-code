import datetime
import os


DB_ACCESS = True
TIMEOUT_LIST = [1, 11, 15]


def parse_timezone(timezone_txt):
    timezone_txt_no_utc = timezone_txt.replace("UTC", "")
    if timezone_txt_no_utc == "":
        timezone_txt_no_utc = "00:00"
    hours, minutes = timezone_txt_no_utc[1:].split(":")
    td = datetime.timedelta(hours=int(hours), minutes=int(minutes))
    td = td if timezone_txt_no_utc[0] == "+" else -td
    offset = datetime.timezone(td)
    return offset


def create_dir(dir_name):
    """Создание директории, если таковой нет.

    Args:
       dir_name(str): Наименование папки
    """
    if not os.path.exists(dir_name):
        os.makedirs(dir_name)
