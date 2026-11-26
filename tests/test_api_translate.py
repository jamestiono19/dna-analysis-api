import pytest

from tests.conftest import PATIENTS, read_fixture
from tests.test_translation import BRIEF_PROTEIN


def test_patient_02_matches_the_example_in_the_brief(post_fasta):
    response = post_fasta("/api/translate", read_fixture("patient_02.fasta"), frame="1")
    assert response.status_code == 200
    assert response.json() == {
        "sequence_id": "patient_02",
        "frame": 1,
        "protein": BRIEF_PROTEIN,
        "length": 81,
        "has_stop_codon": True,
    }


def test_frame_defaults_to_one(post_fasta):
    body = post_fasta("/api/translate", read_fixture("patient_02.fasta")).json()
    assert body["frame"] == 1
    assert body["protein"] == BRIEF_PROTEIN


# Two parametrize lines: runs for every patient in every frame (5 x 3 = 15 runs).
@pytest.mark.parametrize("name", PATIENTS)
@pytest.mark.parametrize("frame", ["1", "2", "3"])
def test_every_patient_in_every_frame(post_fasta, name, frame):
    response = post_fasta("/api/translate", read_fixture(name), frame=frame)
    assert response.status_code == 200
    body = response.json()
    assert body["frame"] == int(frame)
    assert body["length"] == len(body["protein"])
    assert "*" not in body["protein"]


@pytest.mark.parametrize(
    "frame, protein, has_stop",
    [("1", "NGL", False), ("2", "MA", True), ("3", "WP", False)],
)
def test_each_reading_frame(post_fasta, frame, protein, has_stop):
    body = post_fasta("/api/translate", ">s\nAATGGCCTAA", frame=frame).json()
    assert (body["protein"], body["has_stop_codon"]) == (protein, has_stop)


def test_lowercase_input(post_fasta):
    body = post_fasta("/api/translate", ">s\natggcctaa").json()
    assert body["protein"] == "MA"


def test_n_containing_codons_become_x(post_fasta):
    body = post_fasta("/api/translate", ">s\nATGCTNGGN").json()
    assert (body["protein"], body["length"]) == ("MXX", 3)


def test_patient_04_n_blocks_become_x(post_fasta):
    body = post_fasta("/api/translate", read_fixture("patient_04.fasta")).json()
    assert body["protein"].startswith("MSSFVPX")
    assert body["length"] == len(body["protein"])


def test_stop_handling(post_fasta):
    body = post_fasta("/api/translate", ">s\nATGTGAGCC").json()
    assert (body["protein"], body["has_stop_codon"]) == ("M", True)


def test_incomplete_final_codon(post_fasta):
    body = post_fasta("/api/translate", ">s\nATGGCCGC").json()
    assert (body["protein"], body["has_stop_codon"]) == ("MA", False)


def test_no_complete_codon(post_fasta):
    body = post_fasta("/api/translate", ">s\nACGT", frame="3").json()
    assert (body["protein"], body["length"], body["has_stop_codon"]) == ("", 0, False)


def test_length_limit(post_fasta):
    assert post_fasta("/api/translate", ">s\n" + "A" * 1000).status_code == 200
    assert post_fasta("/api/translate", ">s\n" + "A" * 1001).status_code == 400


def test_empty_frame_field_uses_default(post_fasta):
    # FastAPI treats an empty form value as "not sent", so the default applies.
    assert post_fasta("/api/translate", ">s\nATG", frame="").json()["frame"] == 1


@pytest.mark.parametrize("frame", ["0", "4", "-1", "1.5", "abc", " ", "01"])
def test_invalid_frame_returns_422_json(post_fasta, frame):
    response = post_fasta("/api/translate", ">s\nATG", frame=frame)
    assert response.status_code == 422
    assert response.json()["error"]["type"] == "invalid_frame"


@pytest.mark.parametrize("text", [">s\nACGX", ">a\nACG\n>b\nACG", ">s\n"])
def test_invalid_fasta_returns_400_json(post_fasta, text):
    response = post_fasta("/api/translate", text)
    assert response.status_code == 400
    assert response.json()["error"]["type"] == "invalid_fasta"


def test_missing_file_returns_422_json(client):
    response = client.post("/api/translate", data={"frame": "1"})
    assert response.status_code == 422
    assert response.json()["error"]["type"] == "missing_file"
