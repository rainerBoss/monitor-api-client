class Base(Exception):
    """
    Base exception
    """

class RequestError(Base):
    """
    Error when no response was received
    """

class AuthError(Base):
    """
    Parent exception type for errors performing login
    """

class LoginFailed(AuthError):
    """
    This typically occurs if the username or password is invalid.
    """

class MFARequired(AuthError):
    """
    This typically occurs if the user is blocked by not having setup a multi-factor authentication device.
    See Multi-factor authentication for more information on how to setup an multi-factor authentication device.
    """

class GeneralError(Base):
    """
    Parent exception type for general failure states that are not specific to commands or queries.
    """

class SessionSuspended(GeneralError):
    """
    This occurs if another person has authenticated as the user your session belongs to
    as there can only be one active session per user at a time.
    """

class ApiNotAvailable(GeneralError):
    """
    This error occurs on any request to an API endpoint in case the customer system does not have the API option enabled.
    """

class UnhandledException(GeneralError):
    """
    This error occurs if an unhandled exception is triggered in the server.
    """

class InvalidSessionId(GeneralError):
    """
    This occurs if the X-Monitor-SessionId header is either not set or if it contains a session identifier that is not valid.
    """

class CommandError(Base):
    """
    Parent excedption type only for when sending commands to the API via POST requests.
    """

class CommandNotFound(CommandError):
    """
    This occurs when the command you requested could not be found.
    Verify the command URL against the reference documentation and make sure that it is correct.
    """

class CommandValidationFailure(CommandError):
    """
    This occurs when the command handler determines that something is wrong with the input data.
    The message in the response body will contain more information.
    """

class CommandEntityNotFound(CommandError):
    """
    This occurs when the command handler attempts to retrieve an entity that does not exist when processing a command.
    """

class CommandConflict(CommandError):
    """
    This occurs when a command attempts to save an entity that has changed since it was first read by the command processor.
    This can usually be resolved by sending the command again.
    """

class BatchCommandError(CommandError):
    """
    Error when batch command IsSuccessful field is false
    """

class QueryError(Base):
    """
    Parent exception type only for when querying the API via GET requests.
    """

class QueryEntityNotFound(QueryError):
    """
    This occurs when the query provider or entity cannot be found.
    """

class QueryInvalidId(QueryError):
    """
    This occurs when the id parameter of the query cannot be converted to a long value.
    """

class QueryInvalidFilter(QueryError):
    """
    This occurs when an invalid filter clause is provided on the $filter parameter of the query.
    """