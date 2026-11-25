import pytest

from app.errors import InvalidFrameError
from app.services.fasta import parse_fasta
from app.services.translation import CODON_TABLE, translate
from tests.conftest import read_fixture

BRIEF_PROTEIN = "MSSFVPLLYVSRVGTSNRLFSLLTKFTWVSVTRLRNPAEFAACVRHPYLAHSSQSHEHNLALVITSGQSTPDSKGEQNWVS"


def test_codon_table_is_the_standard_code():
    assert len(CODON_TABLE) == 64
    assert CODON_TABLE["ATG"] == "M"
    assert CODON_TABLE["TGG"] == "W"
    assert sorted(codon for codon, aa in CODON_TABLE.items() if aa == "*") == ["TAA", "TAG", "TGA"]


@pytest.mark.parametrize(
    "frame, protein, has_stop",
    [
        (1, "NGL", False),  # AAT GGC CTA + A
        (2, "MA", True),  # ATG GCC TAA
        (3, "WP", False),  # TGG CCT + AA
    ],
)
def test_each_reading_frame(frame, protein, has_stop):
    result = translate("AATGGCCTAA", frame)
    assert result.protein == protein
    assert result.has_stop_codon is has_stop
    assert result.length == len(protein)


def test_default_frame_is_one():
    assert translate("ATGGCC").frame == 1


def test_codon_with_n_becomes_x():
    # CTN would be leucine for any base, but the rule is X for every N codon.
    result = translate("ATGCTNGGN")
    assert result.protein == "MXX"
    assert result.length == 3


@pytest.mark.parametrize("stop", ["TAA", "TAG", "TGA"])
def test_translation_stops_before_first_stop_codon(stop):
    result = translate("ATGGCC" + stop + "GCCTAA")
    assert result.protein == "MA"
    assert result.has_stop_codon is True
    assert "*" not in result.protein


def test_stop_like_codon_with_n_is_not_a_stop():
    result = translate("ATGTANGCC")
    assert result.protein == "MXA"
    assert result.has_stop_codon is False


def test_no_stop_codon():
    result = translate("ATGGCCGCC")
    assert result.has_stop_codon is False


@pytest.mark.parametrize("sequence, protein", [("ATGGC", "M"), ("ATGGCCA", "MA")])
def test_incomplete_final_codon_is_ignored(sequence, protein):
    assert translate(sequence).protein == protein


@pytest.mark.parametrize("sequence, frame", [("A", 1), ("AC", 1), ("ACG", 2), ("ACGT", 3)])
def test_no_complete_codon_gives_empty_result(sequence, frame):
    result = translate(sequence, frame)
    assert (result.protein, result.length, result.has_stop_codon) == ("", 0, False)


def test_stop_as_first_codon_gives_empty_protein_with_stop():
    result = translate("TAAATG")
    assert (result.protein, result.length, result.has_stop_codon) == ("", 0, True)


@pytest.mark.parametrize("frame", [0, 4, -1])
def test_invalid_frame_is_rejected(frame):
    with pytest.raises(InvalidFrameError):
        translate("ATG", frame)


def test_patient_02_matches_the_example_in_the_brief():
    result = translate(parse_fasta(read_fixture("patient_02.fasta")).sequence, 1)
    assert result.protein == BRIEF_PROTEIN
    assert result.length == 81
    assert result.has_stop_codon is True
