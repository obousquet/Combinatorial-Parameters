# CP-D09 source review

**Verdict:** Retain the finite nonempty lopsided bound coVC(H)≤VC(H)+1. Reject the claimed d=n−1 improvement. Repair the preceding cube identity's domain, dimension wording, and full-cube endpoint. Reuse the existing later proof, explicitly taking the complement after projection. Remove the unsupported proposed extension to merely VC-maximal classes; this review neither proves nor refutes that extension.

## Exact source and reusable owners

- `CombinatorialParameters/main.tex:1163–1169`: cube identity, lopsided paragraph, and speculative maximal extension.
- Same source, `ex:maxclasses` at21566 and proof at21700–21718: already states and argues the valid extremal/intersection-closed bound. This is reuse and clarification, not new mathematics. Only the extremal paragraph is repaired; the intersection-closed proof is outside this patch.
- Same source, complement conventions at853–855, dual containment at861–894, extenture/hollow-star proof at966–969: finite cube complement and minimal forbidden labeling/cube dictionary.
- Database `data/parameters/042_covc_dimension.json`: projected hollow-star definition; full cube zero appears explicitly in its evidence. This review does not certify all other fields of that record.
- `PartialCubes/main.tex:577–598`, `sec:ample-lopsided` at8345–8363: ampleness means shattering equals strong shattering; complement and connected/isometric graph contracts.
- `YangDim/ample_cohen_macaulay.tex:1938–1950`, `cor:artin-linkage` at1962–1967: explicit shattering/complement duality and complementary ampleness. These are supporting known contracts; algebraic linkage is not needed for the proof here.

Source fingerprints are in `SOURCE-evidence.json`; exact baseline/replacement/patch hashes and original replacement ranges are in `SOURCE-manifest.json`. No full staged main was written because disk space is constrained.

## Checked argument and endpoint failures

For a nonempty proper finite class on n coordinates, an unrealizable labeling on S has an extension cube of dimension n−|S| inside the complement. Minimal unrealizability is equivalent to maximality of that cube: deleting a specified coordinate enlarges it in that direction. Each one-coordinate-deleted sample being realizable implies that its realizer flips exactly that coordinate in the S-trace, giving the projected hollow star. Thus maximizing |S| equals n minus the minimum dimension of a maximal complementary cube. “Size” in the old lemma cannot mean vertex count. Also H is a family, so the old H∈2^X type is wrong. The full cube has coVC zero but its complement is empty, so the minimum in the old formula is undefined. The patch treats it separately; n=0 consequently has the correct singleton/full-cube endpoint. Empty concept classes are excluded from this lemma, avoiding an unannounced empty-class coVC/VC convention.

For the lopsided bound, take a projected hollow star on S and write E=H|S. Projection preserves ampleness. Its cube complement F is ample and nonempty. The missing center is isolated in F, since its one-coordinate neighbours belong to E. Connectedness forces F to be that singleton; hence E is the whole punctured cube, shattering every proper subset of S. Therefore |S|−1≤VC(H). This is precisely the existing later argument with its complement/projection order made explicit. In general `(complement H)|S` is not the complement of `H|S`; the old prose could be read as this invalid interchange. The patch uses the latter, as required. The same finite-support proof covers the later statement's infinite-domain extremal case when extremality is understood through its finite projections.

The statement that the complement contains “all possible cubes” is false literally and insufficient if it means one cube in every direction: neither establishes that every maximal cube has large dimension. For example H={00} is ample of VC zero but its complement does not contain all edges of the square. The bound itself follows from the hollow-star argument, not that inference.

The alleged exception is directly false: for n≥1, H={0,1}^n minus0^n is ample (every proper coordinate subset is both shattered and strongly shattered by fixing an omitted coordinate to one), with VC n−1 and coVC n. The all-zero sample on all n coordinates is minimally unrealizable. For n=1 this is a singleton with VC zero and coVC one. Thus d+1 remains sharp at the very endpoint where the old paragraph claimed improvement. This uses a standard existing punctured-cube example, not a new family or novelty claim.

## Scope and next actions

Read repo AGENTS and relevant research-knowledge/reviewer guidance. Bounded direct searches covered current and archived CP ledger/inventory text and the indicated PartialCubes/YangDim sources. Registry context failed with “database or disk is full”; no cache rebuild or sibling source mutation was performed. No external acquisition, experiment, broad catalogue completion, or new conjecture campaign was needed.

`SOURCE.patch` replaces two small blocks and `SOURCE-withdrawn.tex` preserves both exact old blocks. The valid early bound points forward to the existing later proof to avoid duplicated arguments. Independent review and parent integration/build remain necessary. No verdict here extends to the nearby infinite-domain examples, other dual-Helly equivalences, the merely-maximal speculation, or full-paper readiness.
