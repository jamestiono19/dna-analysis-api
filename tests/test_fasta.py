import pytest

from app.errors import FastaValidationError
from app.services.fasta import MAX_SEQUENCE_LENGTH, decode_upload, parse_fasta


def test_single_record():
    record = parse_fasta(">seq1\nACGT\n")
    assert record.sequence_id == "seq1"
    assert record.sequence == "ACGT"


def test_sequence_id_is_first_token_of_header():
    assert parse_fasta(">REF_001 synthetic CDS, 300 bp\nACGT").sequence_id == "REF_001"


def test_multiline_blank_lines_crlf_and_surrounding_whitespace():
    record = parse_fasta("\n>s\r\nACG\r\n\r\n   TTN  \r\n\r\n")
    assert record.sequence == "ACGTTN"


def test_lowercase_is_converted_to_uppercase():
    assert parse_fasta(">s\nacgtn").sequence == "ACGTN"


def test_sequence_of_only_n_is_accepted():
    assert parse_fasta(">s\n" + "N" * 1000).sequence == "N" * 1000


def test_length_limit_boundary_is_accepted():
    assert len(parse_fasta(">s\n" + "A" * MAX_SEQUENCE_LENGTH).sequence) == 1000


def test_length_limit_counts_bases_across_lines():
    text = ">s\n" + "\n".join(["A" * 100] * 10)  # 1,000 bases on 10 lines
    assert len(parse_fasta(text).sequence) == 1000


@pytest.mark.parametrize(
    "text, expected_message",
    [
        ("", "no header line"),
        ("\n\n", "no header line"),
        ("ACGT\n", "must start with a header"),
        (">\nACGT", "header is empty"),
        (">   \nACGT", "header is empty"),
        (">s\n", "no sequence"),
        (">s\n\n\n", "no sequence"),
        (">s\nAC GT", "whitespace inside the sequence"),
        (">s\nAC\tGT", "whitespace inside the sequence"),
        (">s\nACGU", "Invalid character 'U'"),
        (">s\nACG-T", "Invalid character '-'"),
        (">s\nACGT*", "Invalid character '*'"),
        (">a\nACGT\n>b\nACGT", "Only one FASTA record"),
        (">a\nACGT\n>", "Only one FASTA record"),
        (">s\n" + "A" * 1001, "The limit is 1000"),
    ],
)
def test_invalid_fasta_is_rejected(text, expected_message):
    with pytest.raises(FastaValidationError) as error:
        parse_fasta(text)
    assert expected_message in error.value.message


def test_invalid_character_position_is_reported():
    with pytest.raises(FastaValidationError) as error:
        parse_fasta(">s\nACGT\nAXG")
    assert "position 6" in error.value.message


def test_decode_removes_byte_order_mark():
    assert decode_upload("\ufeff>s\nACGT".encode("utf-8")).startswith(">s")


def test_decode_rejects_binary_content():
    with pytest.raises(FastaValidationError):
        decode_upload(b"\xff\xfe\x00\x01")
