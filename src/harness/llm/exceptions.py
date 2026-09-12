"""LLM client exceptions."""


class LLMError(Exception):
    """Base exception for LLM client errors."""


class LLMConnectionError(LLMError):
    """Raised when the LLM server cannot be reached."""


class LLMResponseError(LLMError):
    """Raised when the LLM server returns an error response."""
