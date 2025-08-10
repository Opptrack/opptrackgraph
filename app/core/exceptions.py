class LLMException(Exception):
    def __init__(self, message: str):
        self.message = message

    def __str__(self):
        return self.message


class PDFException(Exception):
    def __init__(self, message: str):
        self.message = message

    def __str__(self):
        return self.message


class APIError(Exception):
    """Base class for API-related exceptions."""

    pass


class InvalidAPIKeyError(APIError):
    """Raised when an invalid API key is used."""

    def __init__(self, message="Invalid API key provided"):
        super().__init__(message)


class RateLimitExceededError(APIError):
    """Raised when the API rate limit is exceeded."""

    def __init__(self, message="API rate limit exceeded"):
        super().__init__(message)


class APIRequestError(APIError):
    """Raised for generic API request errors."""

    def __init__(self, message="An error occurred while making an API request"):
        super().__init__(message)


class LatexValidationError(Exception):
    """Raised when LaTeX content fails validation."""

    pass


class LatexStructureError(LatexValidationError):
    """Raised when LaTeX content has structural issues like missing documentclass or environments."""

    pass


class LatexSyntaxError(LatexValidationError):
    """Raised when LaTeX content has syntax issues like unmatched braces or environments."""

    pass


class LatexCompilationError(LatexValidationError):
    """Raised when LaTeX content fails to compile."""

    pass


class LatexReferenceError(LatexValidationError):
    """Raised when LaTeX content has unresolved references or citations."""

    pass


class LatexConversionError(Exception):
    """Raised when LaTeX to PDF conversion fails."""

    pass


class LangGraphNodeError(Exception):
    """Raised when a LangGraph node fails."""

    pass
