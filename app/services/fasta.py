""" Turns the file into text, checks every validation rule and returns a fixed FASTA record."""

from dataclasses import dataclass

from app.errors import FastaValidationError

MAX_SEQUENCE_LENGTH = 1000
MAX_UPLOAD_BYTES = 100_000
ALLOWED_CHARACTERS = frozenset("ACGTNacgtn")

@dataclass(frozen= True)
class FastaRecord:
    sequence_id: str
    sequence: str

def decode_upload(content: bytes) -> str:
    """Turn the uploaded bytes into text, while rejecting oversized or non-text files."""
    if len(content) > MAX_UPLOAD_BYTES:
        raise FastaValidationError(
            f"The file is too large ({len(content)} bytes). Maximum size accepted is {MAX_UPLOAD_BYTES} bytes."
        )
    try:
        # utf-8-sig removes the byte order mark some Windows editors add.
        return content.decode("utf-8-sig")
    except UnicodeDecodeError:
        # 'from None' hides Python's technical error so only our message is shown.
        raise FastaValidationError("The file is not plain UTF-8 text.") from None

def parse_fasta(text: str) -> FastaRecord:
    """Parse exactly one FASTA record and return its id and uppercase sequence."""
    header = None
    sequence_lines = []

    for line_number, raw_line in enumerate(text.splitlines(), start = 1):
        # Remove spaces and line endings at both ends.
        line = raw_line.strip()
        if not line:
            continue # blank lines are allowed

        if line.startswith(">"):
            if header is not None:
                raise FastaValidationError(
                    f"Only one FASTA record is allowed, but a second header was found on line {line_number}."
                )
            # Drop the '>' and keep the rest as the header.
            header = line[1:].strip()
            if not header:
                raise FastaValidationError("The FASTA header is empty. Write an identifier after '>'.")
            continue

        if header is None:
            raise FastaValidationError(
                "Malformed FASTA: the file must start with a header line beginning with '>'."
            )
        if any(character.isspace() for character in line):
            raise FastaValidationError(f"Line {line_number} contains whitespace inside the sequence.")
        sequence_lines.append(line)

    if header is None:
        raise FastaValidationError("Malformed FASTA: no header line beginning with '>' was found.")

    sequence = "".join(sequence_lines)
    if not sequence: 
        raise FastaValidationError("The FASTA record has no sequence.")

    for position, character in enumerate(sequence, start = 1):
        if character not in ALLOWED_CHARACTERS:
            raise FastaValidationError(
                f"Invalid character {character!r} at sequence position {position}."
            )
    if len(sequence) > MAX_SEQUENCE_LENGTH:
        raise FastaValidationError(
            f"The sequence is {len(sequence)} nucleotides long. The limit is {MAX_SEQUENCE_LENGTH}."
        )

    # The id is the first word of the header: 'REF_001 some notes' gives 'REF_001'.
    return FastaRecord(sequence_id = header.split()[0], sequence=sequence.upper())
            