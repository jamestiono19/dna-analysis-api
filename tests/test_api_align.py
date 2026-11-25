import pytest 

from app.services.reference import get_reference
from tests.conftest import PATIENTS, read_fixture

EXPECTED_VARIANTS = {
    "patient_01.fasta": [],
    "patient_02.fasta": [
        {"position": 52, "ref": "C", "alt": "A", "type": "SNV"},
        {"position": 177, "ref": "A", "alt": "T", "type": "SNV"},
        {"position": 245, "ref": "T", "alt": "G", "type": "SNV"},
    ],
    "patient_03.fasta": [
        {"position": 106, "ref": "AAC", "alt": "-", "type": "deletion"},
        {"position": 208, "ref": "A", "alt": "-", "type": "deletion"},
    ],
    "patient_04.fasta": [],  # only N blocks, and N is never an SNV
    "patient_05.fasta": [
        {"position": 18, "ref": "-", "alt": "ATC", "type": "insertion"},
        {"position": 230, "ref": "-", "alt": "T", "type": "insertion"},
    ],
}


def test_patient_02_matches_the_example_in_the_brief(post_fasta):
    response = post_fasta("/api/align", read_fixture("patient_02.fasta"))
    assert response.status_code == 200
    body = response.json()
    assert body["sequence_id"] == "patient_02"
    assert body["reference_id"] == "REF_001"
    assert body["alignment"]["score"] == 294.0
    assert body["alignment"]["identity"] == 0.99
    assert body["variants"] == EXPECTED_VARIANTS["patient_02.fasta"]


@pytest.mark.parametrize("name", PATIENTS)
def test_variant_coordinates_and_grouping_for_each_patient(post_fasta, name):
    response = post_fasta("/api/align", read_fixture(name))
    assert response.status_code == 200
    assert response.json()["variants"] == EXPECTED_VARIANTS[name]


@pytest.mark.parametrize("name", PATIENTS)
def test_full_aligned_strings_are_returned(post_fasta, name):
    alignment = post_fasta("/api/align", read_fixture(name)).json()["alignment"]
    assert "..." not in alignment["reference_aligned"]
    assert alignment["reference_aligned"].replace("-", "") == get_reference().sequence
    assert len(alignment["reference_aligned"]) == len(alignment["query_aligned"])


def test_patient_05_insertion_is_supported_by_returned_alignment(post_fasta):
    alignment = post_fasta("/api/align", read_fixture("patient_05.fasta")).json()["alignment"]
    # insertion at position 18 means after reference base 18
    assert alignment["reference_aligned"][18:21] == "---"
    assert alignment["query_aligned"][18:21] == "ATC"


def test_lowercase_input_gives_the_same_result(post_fasta):
    text = read_fixture("patient_02.fasta")
    header, _, sequence = text.partition("\n")
    upper = post_fasta("/api/align", text).json()
    lower = post_fasta("/api/align", header + "\n" + sequence.lower()).json()
    assert lower == upper


def test_n_heavy_sequence_is_accepted(post_fasta):
    response = post_fasta("/api/align", read_fixture("patient_04.fasta"))
    assert response.status_code == 200
    assert response.json()["alignment"]["identity"] < 0.5


def test_length_limit(post_fasta):
    assert post_fasta("/api/align", ">s\n" + "A" * 1000).status_code == 200
    response = post_fasta("/api/align", ">s\n" + "A" * 1001)
    assert response.status_code == 400
    assert response.json()["error"]["type"] == "invalid_fasta"


@pytest.mark.parametrize(
    "text",
    [
        ">s\nACGU",
        ">a\nACGT\n>b\nACGT",
        ">s\n",
        ">\nACGT",
        "ACGT",
        ">s\nAC GT",
        "",
    ],
)
def test_invalid_fasta_returns_400_json(post_fasta, text):
    response = post_fasta("/api/align", text)
    assert response.status_code == 400
    error = response.json()["error"]
    assert error["type"] == "invalid_fasta"
    assert error["message"]


def test_missing_file_returns_422_json(client):
    response = client.post("/api/align")
    assert response.status_code == 422
    assert response.json()["error"]["type"] == "missing_file"


def test_text_field_instead_of_file_returns_422_json(client):
    response = client.post("/api/align", data={"file": ">s\nACGT"})
    assert response.status_code == 422
    assert "error" in response.json()