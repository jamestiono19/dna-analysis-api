"""Variant effect annotation against reference frame 1 (bonus /api/analyze)."""

from dataclasses import dataclass

from app.services.translation import STOP, translate_codon
from app.services.variants import Variant

DEFINED_BASES = frozenset("ACGT")

SYNONYMOUS = "synonymous"
MISSENSE = "missense"
NONSENSE = "nonsense"
FRAMESHIFT = "frameshift"
INFRAME_INSERTION = "in-frame insertion"
INFRAME_DELETION = "in-frame deletion"
UNDETERMINED = "undetermined"


@dataclass(frozen=True)
class VariantEffect:
    variant: Variant
    effect: str
    ref_codon: str | None = None
    alt_codon: str | None = None
    ref_amino_acid: str | None = None
    alt_amino_acid: str | None = None


def annotate_effects(
    reference: str,
    reference_aligned: str,
    query_aligned: str,
    variants: list[Variant],
) -> list[VariantEffect]:
    # Which query base sits under each reference position.
    query_base_at = _query_base_by_reference_position(reference_aligned, query_aligned)
    effects = []
    for variant in variants:
        if variant.type == "SNV":
            effects.append(_snv_effect(variant, reference, query_base_at, variants))
        else:
            effects.append(_indel_effect(variant))
    return effects


def _query_base_by_reference_position(reference_aligned: str, query_aligned: str) -> dict[int, str]:
    """Map each 1-based reference position to the query base aligned to it ('-' if deleted)."""
    mapping = {}
    position = 0
    for reference_base, query_base in zip(reference_aligned, query_aligned):
        if reference_base == "-":
            continue  # inserted query base, no reference position
        position += 1
        mapping[position] = query_base
    return mapping


def _indel_effect(variant: Variant) -> VariantEffect:
    # How many bases were added or removed.
    length = len(variant.alt) if variant.type == "insertion" else len(variant.ref)
    # Not a multiple of 3, so every codon after it is read in the wrong groups (frameshift).
    if length % 3 != 0:
        return VariantEffect(variant, FRAMESHIFT)
    if variant.type == "insertion":
        return VariantEffect(variant, INFRAME_INSERTION)
    return VariantEffect(variant, INFRAME_DELETION)


def _net_shift_before(variants: list[Variant], position: int) -> int:
    """Inserted minus deleted bases from indels that start before a reference position."""
    shift = 0
    for variant in variants:
        if variant.position >= position:
            continue
        if variant.type == "insertion":
            shift += len(variant.alt)
        elif variant.type == "deletion":
            shift -= len(variant.ref)
    return shift


def _snv_effect(
    variant: Variant,
    reference: str,
    query_base_at: dict[int, str],
    variants: list[Variant],
) -> VariantEffect:
    # Find the start of the group of 3 this position is in. Example: 4, 5 and 6 all give 4.
    codon_start = (variant.position - 1) // 3 * 3 + 1  # first base of the codon, 1-based
    # Positions start at 1 but Python starts at 0, then we subtract 1.
    ref_codon = reference[codon_start - 1:codon_start + 2]
    # The codon is cut off at the end or has an N, so its amino acid is unknown.
    if len(ref_codon) < 3 or any(base not in DEFINED_BASES for base in ref_codon):
        return VariantEffect(variant, UNDETERMINED, ref_codon=ref_codon or None)

    # Every query base aligned to this codon, so several SNVs in one codon are judged together.
    alt_codon = "".join(query_base_at.get(p, "-") for p in range(codon_start, codon_start + 3))
    ref_amino_acid = translate_codon(ref_codon)

    # After a frameshift the reference frame no longer applies.
    if _net_shift_before(variants, codon_start) % 3 != 0:
        return VariantEffect(variant, UNDETERMINED, ref_codon, alt_codon, ref_amino_acid)

    # A gap or an N inside the codon means the new amino acid cannot be known.
    if any(base not in DEFINED_BASES for base in alt_codon):
        return VariantEffect(variant, UNDETERMINED, ref_codon, alt_codon, ref_amino_acid)

    alt_amino_acid = translate_codon(alt_codon)
    if alt_amino_acid == ref_amino_acid:
        effect = SYNONYMOUS
    elif alt_amino_acid == STOP:
        effect = NONSENSE
    else:
        effect = MISSENSE  # includes a stop codon changed into an amino acid (stop loss)
    return VariantEffect(variant, effect, ref_codon, alt_codon, ref_amino_acid, alt_amino_acid)
