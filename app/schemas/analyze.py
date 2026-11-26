from typing import Literal

from pydantic import BaseModel

from app.schemas.common import AlignmentSchema, VariantSchema


class AnnotatedVariantSchema(VariantSchema):
    # the value must be one of these exact words.
    effect: Literal[
        "synonymous",
        "missense",
        "nonsense",
        "frameshift",
        "in-frame insertion",
        "in-frame deletion",
        "undetermined",
    ]
    # These can be empty (None), for example for insertions and deletions.
    ref_codon: str | None = None
    alt_codon: str | None = None
    ref_amino_acid: str | None = None
    alt_amino_acid: str | None = None


class TranslationSchema(BaseModel):
    frame: int
    protein: str
    length: int
    has_stop_codon: bool


class AnalyzeResponse(BaseModel):
    sequence_id: str
    reference_id: str
    alignment: AlignmentSchema
    variants: list[AnnotatedVariantSchema]
    translation: TranslationSchema
