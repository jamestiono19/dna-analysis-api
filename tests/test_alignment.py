import pytest

from app.services.alignment import global_align, pair_score
from app.services.fasta import parse_fasta
from app.services.reference import get_reference
from tests.conftest import PATIENTS, read_fixture


def patient_sequence(name: str) -> str:
    return parse_fasta(read_fixture(name)).sequence


def test_identical_sequences():
    result = global_align("ACGT", "ACGT")
    assert result.score == 4.0
    assert result.identity == 1.0
    assert result.reference_aligned == result.query_aligned == "ACGT"


def test_mismatch_scores_minus_one():
    result = global_align("ACGT", "ACCT")
    assert result.score == 2.0  # 3 matches, 1 mismatch
    assert result.identity == 0.75


def test_each_gap_character_scores_minus_two():
    result = global_align("ACGT", "AT")
    assert result.score == -2.0  # 2 matches, 2 gap characters
    assert result.reference_aligned == "ACGT"
    assert result.query_aligned == "A--T"


def test_n_scores_zero():
    assert pair_score("N", "A") == 0
    assert pair_score("A", "N") == 0
    assert pair_score("N", "N") == 0
    result = global_align("ACGT", "ANGT")
    assert result.score == 3.0
    assert result.query_aligned == "ANGT"  # N is aligned, not gapped


def test_n_against_n_is_not_counted_as_identical():
    assert global_align("NNNN", "NNNN").identity == 0.0


def test_identity_counts_gap_columns():
    result = global_align("ACGTACGT", "ACGT")
    assert len(result.reference_aligned) == 8
    assert result.identity == 0.5  # 4 identical columns out of 8


def test_tie_break_keeps_a_deletion_in_one_piece():
    # "ACGT" fits at both ends of "ACGTACGT"; the gap must stay grouped.
    result = global_align("ACGTACGT", "ACGT")
    assert result.query_aligned == "----ACGT"


def test_tie_break_is_deterministic():
    first = global_align("ACGTTGCA", "ACGTGCA")
    second = global_align("ACGTTGCA", "ACGTGCA")
    assert first == second
    assert first.query_aligned == "ACG-TGCA"


# Run this test once for each patient file.
@pytest.mark.parametrize("name", PATIENTS)
def test_aligned_strings_contain_the_complete_inputs(name):
    reference = get_reference().sequence
    query = patient_sequence(name)
    result = global_align(reference, query)
    assert len(result.reference_aligned) == len(result.query_aligned)
    # Removing the gaps must give back the original sequence.
    assert result.reference_aligned.replace("-", "") == reference
    assert result.query_aligned.replace("-", "") == query
    assert 0.0 <= result.identity <= 1.0


def test_patient_01_is_identical_to_reference():
    result = global_align(get_reference().sequence, patient_sequence("patient_01.fasta"))
    assert result.score == 300.0
    assert result.identity == 1.0
    assert "-" not in result.query_aligned


def test_patient_02_matches_the_example_in_the_brief():
    result = global_align(get_reference().sequence, patient_sequence("patient_02.fasta"))
    assert result.score == 294.0
    assert result.identity == 0.99
