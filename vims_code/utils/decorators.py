def white_list(func):
    func.white_list = True

    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    return wrapper


def need_team_auth(func):
    func.need_team_auth = True

    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    return wrapper
