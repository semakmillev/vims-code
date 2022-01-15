from vims_code.app import ApplicationException, ErrorCodes


class PlayerAlreadyExists(ApplicationException):
    def __init__(self, reason):
        super().__init__(ErrorCodes.ALREADY_EXISTS, reason)


class PlayerNotFound(ApplicationException):
    def __init__(self, reason):
        super().__init__(ErrorCodes.OBJECT_NOT_FOUND, reason, 403)


class WrongSession(ApplicationException):
    def __init__(self, reason):
        super().__init__(ErrorCodes.FORBIDDEN, reason, 401)


class WrongPassword(ApplicationException):
    def __init__(self, reason):
        super().__init__(ErrorCodes.AUTHORIZATION_FAILED, reason, 403)


class SafetyFail(ApplicationException):
    def __init__(self, reason):
        super().__init__(ErrorCodes.FORBIDDEN, reason, 403)