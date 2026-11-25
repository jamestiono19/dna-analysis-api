from pydantic import BaseModel


class TranslateResponse(BaseModel):
    sequence_id: str
    frame: int
    protein: str
    length: int
    has_stop_codon: bool
