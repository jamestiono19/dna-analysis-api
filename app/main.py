from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.errors import FastaValidationError, InputError, InvalidFrameError, MissingFileError
from app.routers import align, translate, analyze
from app.services.reference import get_reference

WEB_DIR = Path(__file__).resolve().parents[1] / "web"

# Which HTTP status and error type each input error becomes.
ERROR_MAPPING = {
    FastaValidationError: (400, "invalid_fasta"),
    MissingFileError: (422, "missing_file"),
    InvalidFrameError: (422, "invalid_frame"),
}


def error_response(status_code: int, error_type: str, message: str) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"error": {"type": error_type, "message": message}},
    )


@asynccontextmanager
async def lifespan(_app: FastAPI):
    get_reference()  # load REF_001 at startup so a broken reference file fails fast
    yield


app = FastAPI(
    title="DNA Sequence Analysis API",
    description="Global alignment with variant detection, and protein translation.",
    lifespan=lifespan,
)
app.include_router(align.router)
app.include_router(translate.router)
app.include_router(analyze.router)


@app.exception_handler(InputError)
async def handle_input_error(_request: Request, exc: InputError) -> JSONResponse:
    status_code, error_type = ERROR_MAPPING.get(type(exc), (400, "invalid_input"))
    return error_response(status_code, error_type, exc.message)


@app.exception_handler(RequestValidationError)
async def handle_request_validation_error(_request: Request, exc: RequestValidationError) -> JSONResponse:
    errors = exc.errors()
    first = errors[0] if errors else {}
    field = ".".join(str(part) for part in first.get("loc", ()) if part != "body") or "request"
    message = f"Invalid value for '{field}': {first.get('msg', 'invalid request')}."
    return error_response(422, "invalid_request", message)


if WEB_DIR.is_dir():
    app.mount("/static", StaticFiles(directory=WEB_DIR), name="static")

    @app.get("/", include_in_schema=False)
    def index() -> FileResponse:
        return FileResponse(WEB_DIR / "index.html")
