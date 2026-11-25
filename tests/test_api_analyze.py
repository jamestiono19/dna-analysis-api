import pytest

from tests.conftest import read_fixture


def effects(post_fasta, name):
    response = post_fasta("/api/analyze", read_fixture(name))
    assert response.status_code == 200
    return [(v["position"], v["type"], v["effect"]) for v in response.json()["variants"]]


def test_patient_02_synonymous_missense_nonsense(post_fasta):
    assert effects(post_fasta, "patient_02.fasta") == [
        (52, "SNV", "synonymous"),  # CGA -> AGA, both R
        (177, "SNV", "missense"),  # AAA (K) -> AAT (N)
        (245, "SNV", "nonsense"),  # TTA (L) -> TGA (stop)
    ]


def test_patient_03_deletions(post_fasta):
    assert effects(post_fasta, "patient_03.fasta") == [
        (106, "deletion", "in-frame deletion"),
        (208, "deletion", "frameshift"),
    ]


def test_patient_05_insertions(post_fasta):
    assert effects(post_fasta, "patient_05.fasta") == [
        (18, "insertion", "in-frame insertion"),
        (230, "insertion", "frameshift"),
    ]


def test_response_includes_frame_1_translation(post_fasta):
    body = post_fasta("/api/analyze", read_fixture("patient_02.fasta")).json()
    assert body["translation"]["frame"] == 1
    assert body["translation"]["length"] == 81
    assert body["alignment"]["score"] == 294.0


@pytest.mark.parametrize("text", [">s\nACGX", ">a\nA\n>b\nA"])
def test_invalid_fasta_returns_400_json(post_fasta, text):
    response = post_fasta("/api/analyze", text)
    assert response.status_code == 400
    assert response.json()["error"]["type"] == "invalid_fasta"
