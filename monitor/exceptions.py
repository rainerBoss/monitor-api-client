class Base(Exception):
    pass


class RequestError(Base):
    pass


class LoginFailed(Base):
    pass


class SessionSuspended(Base):
    pass


class MFARequired(Base):
    pass


class ApiNotAvailable(Base):
    pass


class InternalMonitorException(Base):
    pass


class InvalidSessionId(Base):
    pass


class CommandError(Base):
    pass


class CommandNotFound(CommandError):
    pass


class CommandValidationFailure(CommandError):
    pass


class CommandEntityNotFound(CommandError):
    pass


class CommandConflict(CommandError):
    pass


class BatchCommandError(CommandError):
    pass


class QueryError(Base):
    pass


class QueryEntityNotFound(QueryError):
    pass


class QueryInvalidId(QueryError):
    pass


class QueryInvalidFilter(QueryError):
    pass