"""Variant calling from a pair of aligned strings."""

from dataclasses import dataclass

DEFINED_BASES = frozenset("ACGT")

@dataclass(frozen=True)
class Variant:
    position: int
    ref: str
    alt: str
    type: str # "SNV", "deletion", "insertion"

def call_variants(reference_aligned: str, query_aligned: str) -> list[Variant]:
    variants = []
    reference_position = 0 # number of reference passed by far
    column = 0
    total_columns = len(reference_aligned)

    while column < total_columns:
        reference_base = reference_aligned[column]
        query_base = query_aligned[column]

        if reference_base != "-" and query_base != "-":
            reference_position += 1
            if (
                reference_base != query_base
                and reference_base in DEFINED_BASES
                and query_base in DEFINED_BASES
            ):
                variants.append(Variant(reference_position, reference_base, query_base, "SNV"))
            column += 1

        elif query_base == "-":
            # Deletion: group every consecutive column with gaps in the query.
            end = column
            while end < total_columns and query_aligned[end] == "-":
                end += 1
            deleted = reference_aligned[column:end]
            variants.append(Variant(reference_position + 1, deleted, "-", "deletion"))
            reference_position += len(deleted)
            column = end

        else:
            end = column
            while end < total_columns and reference_aligned[end] == "-":
                end += 1
            inserted = query_aligned[column:end]
            variants.append(Variant(reference_position, "-", inserted, "insertion"))
            column = end

    return sorted(variants, key = lambda variant: variant.position)