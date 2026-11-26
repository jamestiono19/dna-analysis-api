"""Protein translation with the standard genetic code (no libraries)."""

from dataclasses import dataclass

from app.errors import InvalidFrameError

# Standard genetic code. Codons are listed in TCAG order.

_BASES = "TCAG"
_AMINO_ACIDS = "FFLLSSSSYY**CC*WLLLLPPPPHHQQRRRRIIIMTTTTNNKKSSRRVVVVAAAADDEEGGGG"
# Build all 64 three-letter codons in TCAG order and pair each one
# with the letter at the same spot in _AMINO_ACIDS.
CODON_TABLE = {
    first + second + third: _AMINO_ACIDS[index]
    for index, (first, second, third) in enumerate(
        (a, b, c) for a in _BASES for b in _BASES for c in _BASES
    )
}
STOP = "*"
VALID_FRAMES = (1, 2, 3)

@dataclass(frozen=True)
class TranslationResult:
    frame: int
    protein: str
    length: int
    has_stop_codon: bool

def translate_codon(codon: str) -> str:
    """Return the amino acid for one codon. Any codon containing N becomes X."""
    if "N" in codon:
        return "X"
    return CODON_TABLE[codon]

def translate(sequence: str, frame: int = 1):
    if frame not in VALID_FRAMES:
        raise InvalidFrameError(f"Invalid frame {frame!r} frame must be 1, 2 or 3.")

    protein = []
    has_stop_codon = False
    # Range stops early so only complete codons are read
    for start in range(frame - 1, len(sequence) - 2, 3):
        amino_acid = translate_codon(sequence[start:start + 3])
        # End at the first stop codon and leave it out of the protein.
        if amino_acid == STOP:
            has_stop_codon = True
            break
        protein.append(amino_acid)

    protein_text = "".join(protein)
    return TranslationResult(
        frame=frame, 
        protein=protein_text,
        length = len(protein_text),
        has_stop_codon = has_stop_codon,
    )