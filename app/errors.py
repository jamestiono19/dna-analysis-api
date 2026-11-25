"""
Exceptions raised for invalid input.
"""

class InputError(Exception):
    """Base class for every kind of invalid input."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message

class FastaValidationError(InputError):
    """The uploaded text doesn't match exactly one valid FASTA record."""

class MissingFileError(InputError):
    """User doesn't drop any file in the 'file' field."""

class InvalidFrameError(InputError):
    """The reading frame is not 1, 2, or 3."""