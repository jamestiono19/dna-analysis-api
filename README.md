# DNA Sequence Analysis API

A small REST API built with FastAPI for two tasks on DNA sequences:

1. `POST /api/align`: global alignment of a query against the reference `REF_001`, with variant detection.
2. `POST /api/translate`: translation of the query into protein in reading frame 1, 2 or 3.

## Installation

_To be written._

## Running the API

_To be written._

## Example requests

_To be written._

## Running the tests

_To be written._

## Conventions

### Alignment scoring

Global alignment (Needleman-Wunsch), implemented without bioinformatics libraries.

| Case | Score |
|---|---|
| Match (same A/C/G/T base) | +1 |
| Mismatch (different A/C/G/T bases) | -1 |
| Gap (per gap character, linear) | -2 |
| Any column with N (N vs base, or N vs N) | 0 |

N is an unknown base, so it is neither rewarded nor penalised.

### Tie-breaking

When several moves give the same best score during traceback, the order is:
diagonal (match/mismatch) first, then gap in the query (deletion), then gap in the reference (insertion).
The same input always gives the same alignment.

### Identity

identity = identical A/C/G/T columns / all alignment columns (gaps and N columns included).
N/N does not count as a match. The value is between 0 and 1.

### Variants

- Types: `SNV`, `insertion`, `deletion`. No variants gives `[]`.
- SNV and deletion positions are 1-based reference coordinates.
- Deletion: position is the first deleted base, `ref` is the deleted bases, `alt` is `-`.
- Insertion: position is the reference base before the insertion (0 means before base 1), `ref` is `-`, `alt` is the inserted bases.
- Consecutive inserted or deleted bases are grouped into one event, and events are sorted by position.
- An SNV is only called between two different A/C/G/T bases. A column with N is never an SNV.

### Errors

Every error returns JSON in the same shape:

    {"error": {"type": "...", "message": "..."}}

- 400: the uploaded file is not a valid FASTA (bad characters, multiple records, empty sequence, too long, etc.)
- 422: the request itself is wrong (missing `file` field, `frame` not 1, 2 or 3)

## Assumptions

_To be written._

## Limitations

_To be written._