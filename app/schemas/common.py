"""Schemas shared by more than one endpoint."""

from typing import Literal

from pydantic import BaseModel


class AlignmentSchema(BaseModel):
    score: float
    identity: float
    reference_aligned: str
    query_aligned: str


class VariantSchema(BaseModel):
    position: int
    ref: str
    alt: str
    type: Literal["SNV", "insertion", "deletion"]


class ErrorDetail(BaseModel):
    type: str
    message: str


class ErrorResponse(BaseModel):
    error: ErrorDetail


# Error examples shown on the page.
ERROR_RESPONSES = {
    400: {"model": ErrorResponse, "description": "Invalid FASTA file"},
    422: {"model": ErrorResponse, "description": "Missing file or invalid request field"},
}
