"""Request helpers shared by the routers."""

from fastapi import UploadFile

from app.errors import InvalidFrameError, MissingFileError
from app.services.fasta import FastaRecord, decode_upload, parse_fasta


def read_fasta_upload(file: UploadFile | None) -> FastaRecord:
    if file is None:
        raise MissingFileError("No file was uploaded. Send the FASTA file in the multipart field 'file'.")
    return parse_fasta(decode_upload(file.file.read()))


def parse_frame(raw_frame: str | None) -> int:
    """Read the optional 'frame' form field. Missing means frame 1."""
    if raw_frame is None:
        return 1
    value = raw_frame.strip()
    if value not in ("1", "2", "3"):
        raise InvalidFrameError(f"Invalid frame {raw_frame!r}: frame must be 1, 2 or 3.")
    return int(value)
