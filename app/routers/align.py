from dataclasses import asdict
from typing import Annotated

from fastapi import APIRouter, File, UploadFile

from app.routers.common import read_fasta_upload
from app.schemas.align import AlignResponse
from app.schemas.common import ERROR_RESPONSES, AlignmentSchema, VariantSchema
from app.services.alignment import global_align
from app.services.reference import get_reference
from app.services.variants import call_variants

router = APIRouter(prefix="/api", tags=["alignment"])


@router.post("/align", response_model=AlignResponse, responses=ERROR_RESPONSES)
# The file is allowed to be missing here, so we can send our own clear 'missing file' error.
def align(file: Annotated[UploadFile | None, File()] = None) -> AlignResponse:
    """Globally align one FASTA sequence to REF_001 and list its variants."""
    query = read_fasta_upload(file)
    reference = get_reference()

    alignment = global_align(reference.sequence, query.sequence)
    variants = call_variants(alignment.reference_aligned, alignment.query_aligned)

    return AlignResponse(
        sequence_id=query.sequence_id,
        reference_id=reference.sequence_id,
        # asdict turns the result into a dictionary, and ** passes each key as a named value.
        alignment=AlignmentSchema(**asdict(alignment)),
        variants=[VariantSchema(**asdict(variant)) for variant in variants],
    )
