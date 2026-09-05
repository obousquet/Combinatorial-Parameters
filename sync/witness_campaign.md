# Witness review — 2026-09-05

The completion pass screened every established direct relationship, including
relations omitted by graph reduction. The reproducible remaining queue is
[relationship_witness_queue.json](relationship_witness_queue.json).
Regenerate it with:

    python3 sync/audit_relationship_witnesses.py --data-dir data --check \
      --output sync/relationship_witness_queue.json

## Completed changes

- Added 39 witnesses to previously witnessless relationships: 34 unbounded
  families and five finite strict examples.
- Upgraded 57 existing strict witnesses to unbounded affine separations, and
  classified one legacy witness as unbounded.
- Separately, the sharper logarithmic effective-range upper bound for dual
  Littlestone dimension upgrades its former strict witness to unbounded.
- All promotions use inspected endpoint value proofs (and an established
  finite-class equality where needed). A comparison of growth-category labels
  alone was not treated as a proof. Certificates specify a large-enough family
  range; the tournament witness uses primes congruent to 3 modulo 4, and the
  k-block witness fixes k before sending n to infinity.

The new audit only proposes candidates. Its growth categories may describe
one-sided bounds; proposed reverse paths can have additional scope conditions.
Those conditions must be checked before either is used as a certificate.
The check mode also rejects an unbounded witness with a recorded reverse
affine path pending scope review. There are no such conflicts in this batch.

## Strict gaps bounded in the reverse direction

These eight established strict edges already have compatible reverse affine
bounds, now mentioned in their relationship details. No additional transitive
relationship records were created.

| Edge ID | Reverse control | Existing evidence IDs |
|---|---|---|
| 64 | Projected average degree ≤ 2 projected minimum degree | 62, 78 |
| 68 | Dual sign rank ≤ 2 VC + 1 | 69, including its precise affine statement |
| 78 | Projected minimum degree ≤ 2 VC | 64, 62 |
| 97 | Path dimension ≤ 2 threshold dimension | 96 |
| 146 | Diameter ≤ 2 Hamming radius | 124 |
| 213 | Dual antipodal VC ≤ 2 dual VC + 1 | 215 |
| 284 | Littlestone ≤ 2 randomized Littlestone | 285 |
| 341 | Monotonic co-VC ≤ star number + 1 | 342 |

## Remaining work

Among established non-equality, non-incomparability records, 41 have no
witness, 84 have only strict witnesses, and seven retain legacy witness
classification. Eight of the 84 strict cases are excluded from unbounded-gap
search by the reverse controls above.

There are no unused integer-separation or growth-category leads in the
current paired benchmark values for witnessless records, and no unused
growth-category leads for strict records. This is exhaustion of this finite
benchmark screen, not proof that further witnesses do not exist.

The reduced graph still has 26 witnessless edges outside reciprocal affine
blocks. Important unresolved examples include labeled compression versus VC,
order compression versus projected RTD, and positive-characteristic versus characteristic-zero
Yang dimension. These need additional families, values, or proofs.

The witness improvements localize all three previously protected transitive
bypasses to stronger witnessed paths. The graph consequently removes those
three redundant overlays; its reduction audit reports no unresolved bypass.

## Follow-up correction and research campaign

Records #46 and #446 used the full cube's values $n$ and $\lceil n/2\rceil$
to claim unbounded separation. Their additive difference grows but their
ratio stays bounded; both witnesses are now strict. The audit rejects
bounded normalized ratios for a narrow whitelist of exact endpoint formulas,
even if a prose certificate asserts otherwise. Unrecognized expressions and
growth-category leads still require mathematical review.

The systematic follow-up is owned by the survey repository:
`~/latex/CombinatorialParameters/conjectures/parameter_separations.md`, with
its generated root `dashboard.html`. The database remains authoritative for
accepted facts and witnesses.

The next campaign round resolves the positive projection hierarchy by proving
$\mathrm{RTD}^{+p}=\mathrm{NCTD}^{+p}=d_{\max}^{+p}$ on finite classes.
Relationships #457 and #461 are now equalities, so both witness searches
are closed. The canonical proof is survey Proposition
`prop:positive-projection-collapse`; the database regression is
`sync/verify_positive_projection_collapse.py`.

The constrained-tree round adds the cube--half-interval product, with exact
database-owned values and proofs. At fixed $k$, its $(k-1)$-cube slice
separates prefix-$k$ from $k$-block by an unbounded ratio (records #494/#495)
and $k$-block from VC strictly (record #200). The latter ratio remains
bounded. The independent fibre-recursion check covers 84 bounded cases;
the general result rests on the proof, not on this finite census.

The branching batch-tree construction strengthens #58, #200, #205 and #355
from strict to unbounded. At fixed construction width $b$, VC is $b$ and
$B_b=\mathrm{PL}_b=bn$; every larger query block size has value $b$.
Thus even an arbitrary finite-valued VC-only bound for repeated-block depth
is impossible. The database owns the definition and value proofs; survey
Corollary `prop:branching-batch-separations` records the consequences.

The Anchored Torsion Class establishes strict field dependence of Yang
dimension: characteristic two gives four, while characteristic zero and all
odd characteristics give three. Relationship #227 is now witnessed explicitly
at the parameter choice $p=2$; #507 records the default-field comparison.
Neither witness is unbounded, and the same class does not separate an odd
characteristic from zero. The full proof and exact values are database-owned.
