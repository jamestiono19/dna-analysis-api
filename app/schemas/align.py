from pydantic import BaseModel

from app.schemas.common import AlignmentSchema, VariantSchema

class AlignResponse(BaseModel):
    sequence_id: str
    reference_id: str
    alignment: AlignmentSchema
    variants: list[VariantSchema]
