class ResearchError(Exception):
    """A research step failed in a way the graph can route."""

    def __init__(self, message: str, *, retryable: bool = True):
        super().__init__(message)
        self.retryable = retryable
