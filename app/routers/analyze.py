from dataclasses import asdict
from typing import Annotated

from fastapi import APIRouter, File, UploadFile

from app.routers.common import read_fasta_upload
from app.schemas.analyze import AnalyzeResponse, AnnotatedVariantSchema, TranslationSchema
from app.schemas.common import ERROR_RESPONSES, AlignmentSchema
from app.services.alignment import global_align
from app.services.effects import annotate_effects
from app.services.reference import get_reference
from app.services.translation import translate
from app.services.variants import call_variants

router = APIRouter(prefix="/api", tags=["analysis"])


@router.post("/analyze", response_model=AnalyzeResponse, responses=ERROR_RESPONSES)
def analyze(file: Annotated[UploadFile | None, File()] = None) -> AnalyzeResponse:
    """Align, translate (frame 1) and annotate variant effects against reference frame 1."""
    query = read_fasta_upload(file)
    reference = get_reference()

    alignment = global_align(reference.sequence, query.sequence)
    variants = call_variants(alignment.reference_aligned, alignment.query_aligned)
    effects = annotate_effects(
        reference.sequence, alignment.reference_aligned, alignment.query_aligned, variants
    )
    translation = translate(query.sequence, frame=1)

    # Join each variant's basic fields with its effect details into one object.
    annotated = [
        AnnotatedVariantSchema(
            **asdict(effect.variant),
            effect=effect.effect,
            ref_codon=effect.ref_codon,
            alt_codon=effect.alt_codon,
            ref_amino_acid=effect.ref_amino_acid,
            alt_amino_acid=effect.alt_amino_acid,
        )
        for effect in effects
    ]

    return AnalyzeResponse(
        sequence_id=query.sequence_id,
        reference_id=reference.sequence_id,
        alignment=AlignmentSchema(**asdict(alignment)),
        variants=annotated,
        translation=TranslationSchema(**asdict(translation)),
    )
