from typing import Annotated

from fastapi import APIRouter, File, Form, UploadFile

from app.routers.common import parse_frame, read_fasta_upload
from app.schemas.common import ERROR_RESPONSES
from app.schemas.translate import TranslateResponse
from app.services.translation import translate as translate_sequence

router = APIRouter(prefix="/api", tags=["translation"])


@router.post("/translate", response_model=TranslateResponse, responses=ERROR_RESPONSES)
def translate(
    file: Annotated[UploadFile | None, File()] = None,
    frame: Annotated[str | None, Form()] = None,
) -> TranslateResponse:
    """Translate one FASTA sequence to protein in reading frame 1, 2 or 3."""
    # frame is read as text so values like "abc" or "1.5" get our own error message.
    frame_number = parse_frame(frame)
    query = read_fasta_upload(file)
    result = translate_sequence(query.sequence, frame_number)

    return TranslateResponse(
        sequence_id=query.sequence_id,
        frame=result.frame,
        protein=result.protein,
        length=result.length,
        has_stop_codon=result.has_stop_codon,
    )
