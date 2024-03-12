from typing import Generic, TypeVar

T = TypeVar("T")

class Outcome(Generic[T]):
    INVALID_TIME = 0
    INVALID_DATE = 1
    NO_LOCATION_PROVIDED = 2
    NO_TIME_PROVIDED = 3
    INVALID_LOCATION = 4
    
    result: T | None
    error: str | None
    errorType: int | None

    def __init__(
        self, result: T = None, error: str = None, errorType: int = None
    ) -> None:
        if error == result:
            raise Exception("The error and the result are the same")
        if error != None and result != None:
            raise Exception("There can't be an error and not an error at the same time")
        if error != None and errorType == None:
            raise Exception("Error message requires an error Type")
        self.error, self.result, self.errorType = error, result, errorType

    def __bool__(self):
        return self.error == None

    def __repr__(self) -> str:
        if self.error:
            return self.error
        return str(self.result)
