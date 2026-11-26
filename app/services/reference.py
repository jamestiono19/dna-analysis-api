"""Loads the reference sequence REF_001 from app/data/reference.fasta."""

from functools import lru_cache
from pathlib import Path

from app.services.fasta import FastaRecord, parse_fasta

REFERENCE_PATH = Path(__file__).resolve().parents[1] / "data" / "reference.fasta"

# Remember the result of the first call, so the file is read only once.
@lru_cache(maxsize=1)
def  get_reference() -> FastaRecord:
    """Read and validate the reference data once, then reuse it for later requests."""
    return parse_fasta(REFERENCE_PATH.read_text(encoding="utf-8"))