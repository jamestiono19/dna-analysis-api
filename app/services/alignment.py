"""Global alignment (Needleman-Wunsch) written without bioinformatics libraries.

I preserve three score tables rooted from Gotoh's layout which consists of :
- One for alignments that end in a match/mismatch column.
- One that ends in a deletion.
- One that ends in an insertion. 

Every gap character stil costs the same GAP_SCORE, thus the scores are identical to plain Needleman-Wunsch.

The extra tables exist to break ties. When the aligner is already in a gap and two paths score the same,
it keeps extending that gap. This gives one grouped insert-deletion instead of several scattered single base gaps, 
which makes the variant easier to read."""

from dataclasses import dataclass

# Scoring rule for sequence alignment comparison 
MATCH_SCORE = 1
MISMATCH_SCORE = -1
GAP_SCORE = -2 
N_SCORE = 0

"""
MATCH = column with two bases 
DELETION = gap in the query
INSERTION = gap in the reference
"""

MATCH, DELETION, INSERTION = 0, 1, 2 

# Tie-break order, highest priority comes first.
MATCH_PRIORITY = (MATCH, DELETION, INSERTION) # use for the final cell
DELETION_PRIORITY = (DELETION, MATCH, INSERTION) # expand the open deletion first
INSERTION_PRIORITY = (INSERTION, MATCH, DELETION) # expand the open insertion first

IMPOSSIBLE = -(10**9) # fills cells that cannot exist
DEFINED_BASES = frozenset("ACGT")

@dataclass(frozen = True)
class AlignmentResult:
    score: float
    identity: float
    reference_aligned: str
    query_aligned: str

def pair_score(reference_base: str, query_base: str) -> int:
    if reference_base == "N" or query_base == "N":
        return N_SCORE
    return MATCH_SCORE if reference_base == query_base else MISMATCH_SCORE

def calculate_identity(reference_aligned: str, query_aligned: str) -> float:
    """Identical A/C/G/T columns divided by all columns, including gaps and N."""
    if not reference_aligned: 
        return 0.0 
    identical = sum(
        1 for r, q in zip(reference_aligned, query_aligned)
        if r == q and r in DEFINED_BASES 
    )
    return identical / len(reference_aligned)

def _best(candidates: tuple[int, int, int], priority: tuple[int, int, int]) -> tuple[int, int]:
    """Return (score, state) of the highest candidate, breaking ties by priority."""
    best_state = priority[0]
    # Only a higher score replaces the current pick, so on a tie the one listed first wins.
    for state in priority[1:]:
        if candidates[state] > candidates[best_state]:
            best_state = state
    return candidates[best_state], best_state

def global_align(reference: str, query: str) -> AlignmentResult:
    rows, cols = len(reference), len(query)

    # Make a grid with one extra row and column for the start.
    def table(value: int) -> list[list[int]]:
        return [[value] * (cols + 1) for _ in range(rows + 1)]

    # best score of reference[:1] vs query[:j] ending in that state
    scores = [table(IMPOSSIBLE), table(IMPOSSIBLE), table(IMPOSSIBLE)]

    # state of the previous column on the best path
    came_from = [table(MATCH), table(MATCH), table(MATCH)]

    # Starting point: nothing aligned yet, so the score is 0.
    scores[MATCH][0][0] = 0
    # First column: reference bases against nothing, so every step is a gap.
    for i in range(1, rows + 1):
        scores[DELETION][i][0] = i * GAP_SCORE
        # The first gap comes from the start cell, the later ones continue the same gap.
        came_from[DELETION][i][0] = DELETION if i > 1 else MATCH
    # First row: query bases against nothing, also all gaps.
    for j in range(1, cols + 1):
        scores[INSERTION][0][j] = j * GAP_SCORE
        came_from[INSERTION][0][j] = INSERTION if j > 1 else MATCH

    # Fill the rest of the grid one cell at a time.
    # Each cell keeps the best score for each of the three ways to reach it.
    for i in range(1, rows + 1):
        reference_base = reference[i - 1]
        for j in range(1, cols + 1): 
            # Diagonal step: the reference base and the query base share one column.
            diagonal = (
                scores[MATCH][i - 1][j - 1], 
                scores[DELETION][i - 1][j - 1],
                scores[INSERTION][i - 1][j - 1],
            )
            best, state = _best(diagonal, MATCH_PRIORITY)
            scores[MATCH][i][j] = best + pair_score(reference_base, query[j - 1])
            came_from[MATCH][i][j] = state

            # Step down: a reference base with a gap in the query (deletion).
            above = (
                scores[MATCH][i - 1][j],
                scores[DELETION][i - 1][j],
                scores[INSERTION][i - 1][j],
            )
            best, state = _best(above, DELETION_PRIORITY)
            scores[DELETION][i][j] = best + GAP_SCORE
            came_from[DELETION][i][j] = state

            # Step right: a query base with a gap in the reference (insertion).
            left = (
                scores[MATCH][i][j - 1],
                scores[DELETION][i][j - 1],
                scores[INSERTION][i][j - 1],
            )
            best, state = _best(left, INSERTION_PRIORITY)
            scores[INSERTION][i][j] = best + GAP_SCORE
            came_from[INSERTION][i][j] = state

    # The bottom-right cell holds the best score for the full sequences.
    final = (scores[MATCH][rows][cols], scores[DELETION][rows][cols], scores[INSERTION][rows][cols])
    final_score, state = _best(final, MATCH_PRIORITY)

    # Walk back from the bottom-right corner to rebuild the alignment.
    reference_aligned, query_aligned = [], []
    i, j = rows, cols
    while i > 0 or j > 0:
        # Note where this step came from before we move.
        previous_state = came_from[state][i][j]
        if state == MATCH:
            reference_aligned.append(reference[i - 1])
            query_aligned.append(query[j - 1])
            i, j = i - 1, j - 1
        elif state == DELETION:
            reference_aligned.append(reference[i - 1])
            query_aligned.append("-")
            i -= 1
        else:
            reference_aligned.append("-")
            query_aligned.append(query[j - 1])
            j -= 1
        state = previous_state 

    # We built the strings from the end, so flip them back to normal order.
    reference_text = "".join(reversed(reference_aligned))
    query_text = "".join(reversed(query_aligned))
    return AlignmentResult(
        score = float(final_score), 
        identity = calculate_identity(reference_text, query_text),
        reference_aligned = reference_text, 
        query_aligned = query_text,
    )
