from app.services.variants import Variant, call_variants


def test_no_variants_returns_empty_list():
    assert call_variants("ACGT", "ACGT") == []


def test_snv_uses_one_based_reference_position():
    assert call_variants("ACGT", "AGGT") == [Variant(2, "C", "G", "SNV")]


def test_n_is_never_an_snv():
    assert call_variants("ACGT", "ANGT") == []
    assert call_variants("ANGT", "ACGT") == []


def test_consecutive_deleted_bases_are_one_event():
    assert call_variants("ACGTTA", "AC---A") == [Variant(3, "GTT", "-", "deletion")]


def test_deletion_at_start():
    assert call_variants("ACGT", "--GT") == [Variant(1, "AC", "-", "deletion")]


def test_deletion_at_end():
    assert call_variants("ACGT", "AC--") == [Variant(3, "GT", "-", "deletion")]


def test_separate_deletions_are_not_merged():
    assert call_variants("ACGTAC", "A-G-AC") == [
        Variant(2, "C", "-", "deletion"),
        Variant(4, "T", "-", "deletion"),
    ]


def test_consecutive_inserted_bases_are_one_event():
    assert call_variants("AC--GT", "ACTTGT") == [Variant(2, "-", "TT", "insertion")]


def test_insertion_before_first_base_is_position_zero():
    assert call_variants("--ACGT", "GGACGT") == [Variant(0, "-", "GG", "insertion")]


def test_insertion_after_last_base():
    assert call_variants("ACGT--", "ACGTAA") == [Variant(4, "-", "AA", "insertion")]


def test_deletion_shifts_later_coordinates():
    # After deleting reference base 2, the SNV is still at reference position 4.
    assert call_variants("ACGTA", "A-GAA") == [
        Variant(2, "C", "-", "deletion"),
        Variant(4, "T", "A", "SNV"),
    ]


def test_insertion_does_not_shift_later_coordinates():
    assert call_variants("AC-GTA", "ACTGAA") == [
        Variant(2, "-", "T", "insertion"),
        Variant(4, "T", "A", "SNV"),
    ]


def test_mixed_events_are_sorted_by_position():
    variants = call_variants("AC-GTACG", "ATAGT-CG")
    assert variants == [
        Variant(2, "C", "T", "SNV"),
        Variant(2, "-", "A", "insertion"),
        Variant(5, "A", "-", "deletion"),
    ]
