from app.services.alignment import global_align
from app.services.effects import annotate_effects
from app.services.variants import call_variants

# ATG AAA TTT GGG TAA  ->  M K F G stop
REFERENCE = "ATGAAATTTGGGTAA"


def effects_for(query: str):
    alignment = global_align(REFERENCE, query)
    variants = call_variants(alignment.reference_aligned, alignment.query_aligned)
    return annotate_effects(REFERENCE, alignment.reference_aligned, alignment.query_aligned, variants)


def test_synonymous():
    # Writing (effect,) checks that there is exactly one result.
    (effect,) = effects_for("ATGAAGTTTGGGTAA")  # AAA -> AAG, both K
    assert effect.effect == "synonymous"
    assert (effect.ref_codon, effect.alt_codon) == ("AAA", "AAG")


def test_missense():
    (effect,) = effects_for("ATGAAATTAGGGTAA")  # TTT (F) -> TTA (L)
    assert effect.effect == "missense"
    assert (effect.ref_amino_acid, effect.alt_amino_acid) == ("F", "L")


def test_nonsense():
    (effect,) = effects_for("ATGTAATTTGGGTAA")  # AAA (K) -> TAA (stop)
    assert effect.effect == "nonsense"


def test_two_snvs_in_one_codon_are_judged_together():
    effects = effects_for("ATGCCATTTGGGTAA")  # AAA -> CCA (P)
    assert [e.effect for e in effects] == ["missense", "missense"]
    assert all(e.alt_codon == "CCA" for e in effects)


def test_n_in_the_same_codon_makes_snv_undetermined():
    (effect,) = effects_for("ATGANTTTTGGGTAA")  # AAA -> ANT
    assert effect.variant.position == 6
    assert effect.effect == "undetermined"


def test_frameshift_and_inframe_deletion():
    assert [e.effect for e in effects_for("ATGAATTTGGGTAA")] == ["frameshift"]
    assert [e.effect for e in effects_for("ATGTTTGGGTAA")] == ["in-frame deletion"]


def test_frameshift_and_inframe_insertion():
    assert [e.effect for e in effects_for("ATGAAAGTTTGGGTAA")] == ["frameshift"]
    assert [e.effect for e in effects_for("ATGAAACCCTTTGGGTAA")] == ["in-frame insertion"]


def test_snv_after_uncompensated_frameshift_is_undetermined():
    reference = "ATGAAACCCGGGTTTAAATAA"
    query = "ATGAACCCGGGTATAAATAA"  # one A deleted, later T -> A at position 14
    alignment = global_align(reference, query)
    variants = call_variants(alignment.reference_aligned, alignment.query_aligned)
    effects = annotate_effects(reference, alignment.reference_aligned, alignment.query_aligned, variants)
    by_type = {e.variant.type: e.effect for e in effects}
    assert by_type == {"deletion": "frameshift", "SNV": "undetermined"}
