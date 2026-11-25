# DNA Sequence Analysis API

A small REST API built with FastAPI for two tasks on DNA sequences:

1. `POST /api/align`: global alignment of a query against the reference `REF_001`, with variant detection.
2. `POST /api/translate`: translation of the query into protein in reading frame 1, 2 or 3.

## Project structure

```
app/
  main.py          app setup, error handlers, web page
  errors.py        input error classes
  routers/         HTTP layer: reads the request, calls services
  services/        all logic: FASTA, alignment, variants, translation, effects
  schemas/         Pydantic response models
  data/            reference.fasta (REF_001)
web/               plain HTML/CSS/JS interface
tests/             pytest suite and the five patient FASTA files
```

## Installation

Requires Python 3.11 or newer (developed on 3.14).

```bash
git clone https://github.com/jamestiono19/dna-analysis-api.git
cd dna-analysis-api
python -m venv .venv
# Windows:      .venv\Scripts\activate
# macOS/Linux:  source .venv/bin/activate
pip install -r requirements.txt
```

## Running the API

```bash
uvicorn app.main:app --port 8000
```
- API docs: http://localhost:8000/docs
- Web interface: http://localhost:8000/

### With Docker

```bash
docker build -t dna-analysis-api .
docker run -p 8000:8000 dna-analysis-api
```

## Requests Protocol

Run these from the repository root.

```bash
curl.exe -X POST http://localhost:8000/api/align -F "file=@tests/fixtures/patient_02.fasta"

curl.exe -X POST http://localhost:8000/api/translate -F "file=@tests/fixtures/patient_02.fasta" -F "frame=1"

curl.exe -X POST http://localhost:8000/api/analyze -F "file=@tests/fixtures/patient_02.fasta"
```

Example response for `patient_02` (the API returns both aligned strings in full):

```json
{
  "sequence_id": "patient_02",
  "reference_id": "REF_001",
  "alignment": {"score": 294.0, "identity": 0.99, "reference_aligned": "ATGAGTTCG...", "query_aligned": "ATGAGTTCG..."},
  "variants": [
    {"position": 52, "ref": "C", "alt": "A", "type": "SNV"},
    {"position": 177, "ref": "A", "alt": "T", "type": "SNV"},
    {"position": 245, "ref": "T", "alt": "G", "type": "SNV"}
  ]
}
```

## Running the tests

```bash
pytest -v
```

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

Several alignments can share the best score. The aligner keeps three score tables (the last column is a
match/mismatch, a deletion or an insertion). Every gap character still costs -2, so the score is the same as
plain Needleman-Wunsch. The tables only decide ties:

- Inside a gap, extending the same gap is preferred, so a tied insert-delete stays as one grouped event.
- Otherwise the order is: match/mismatch, then deletion, then insertion.

Traceback runs from the end of the sequences, so a tied indel is placed as far to the left as possible.
For example, `ACGTTGCA` against `ACGTGCA` gives `ACG-TGCA`. The same input always gives the same alignment.

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

### Translation

- Standard genetic code. Frame 1 starts at nucleotide 1, frame 2 at 2, frame 3 at 3.
- The given strand is translated directly: no start codon search, no reverse complement.
- Only complete codons are translated; 1 or 2 trailing nucleotides are ignored.
- Any codon containing N becomes `X`.
- Translation stops before the first TAA, TAG or TGA, and `*` is never returned.
  A codon such as `TAN` is `X`, not a stop.
- `has_stop_codon` is true only if a stop was reached. `length` is `len(protein)`, including X.
- If the frame leaves no complete codon, the result is `""`, length 0, `has_stop_codon` false.

### Errors

Every error returns JSON in the same shape:

```json
{"error": {"type": "invalid_fasta", "message": "Invalid character 'U' at sequence position 4. Only A, C, G, T and N are allowed."}}
```

| Status | `type` | When |
|---|---|---|
| 400 | `invalid_fasta` | The file is not one valid FASTA record |
| 422 | `missing_file` | No file in the `file` field |
| 422 | `invalid_frame` | `frame` is not 1, 2 or 3 |
| 422 | `invalid_request` | Any other invalid request field |

## Variant effects

Returns the alignment, the variants with an `effect` field, and the frame-1 translation of the query.
Effects are judged against reference frame 1.

| Variant | Effect |
|---|---|
| SNV, same amino acid | `synonymous` |
| SNV, new stop codon | `nonsense` |
| SNV, different amino acid | `missense` |
| Insertion or deletion, length not a multiple of 3 | `frameshift` |
| Insertion or deletion, length a multiple of 3 | `in-frame insertion` / `in-frame deletion` |

How unclear cases are handled:

- **Several SNVs in one codon** are applied together. Each of them gets the effect of the combined codon.
- **Ambiguous codons**: if the query codon has an N or a gap, the SNV is `undetermined`.
- **After a frameshift**: an SNV after an insert-delete that has not been compensated (net shift not a multiple of 3)
  is `undetermined`, because the reference frame no longer applies.
- **Stop loss**: a stop codon changed into an amino acid is reported as `missense`, since the list has
  no stop-loss type. The `ref_amino_acid` (`*`) and `alt_amino_acid` fields show what happened.
- Insert-deletions are classified by length only. Their effect on nearby codons is not modelled.

## Assumptions

- The query is the forward strand of the same fragment as `REF_001`, and the reference frame starts at base 1.
- The reference is loaded by the server from `app/data/reference.fasta` and is not sent in the request.
- A missing `frame` field, or an empty one, means frame 1. FastAPI treats an empty form value as not sent.
- Status 400 is used for a bad file and 422 for a bad request.