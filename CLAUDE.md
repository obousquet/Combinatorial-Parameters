# Combinatorial Parameters Database

This repository is the structured-data and published-website counterpart of
the LaTeX survey at `~/latex/CombinatorialParameters`.  It records
combinatorial parameters, classes of set families, relationships between
parameters, assigned values, and bibliography entries.

## Repository roles

- `data/` is the editable database source of truth for the website.
  - `classes/`, `parameters/`, `relationships/`, and `values/` contain schemas
    and JSON records.
  - `main.json` declares site metadata and the Hasse graph.
  - `make_graph.py` is this repository's graph hook: it selects, reduces, and
    styles the parameter relationships.
- `docs/` is generated static output, committed because GitHub Pages serves it
  from the `main` branch's `/docs` directory. Do not edit it by hand.
- `~/code/math_database` contains the reusable website code. In particular,
  `generate_website.py` builds the site and `render_graph_utils.py` implements
  the shared interactive graph renderer.
- `~/latex/CombinatorialParameters` is the corresponding LaTeX survey. The
  database and LaTeX material should describe the same mathematical objects
  and results. `sync/ownership.json` declares which repository is authoritative
  for each shared kind of information.

## Editing data

- Preserve the schemas in `data/*/schema.json`; use existing IDs and
  cross-references such as `#parameters/<short_name>`.
- `definition` is the single authoritative full, self-contained definition for
  a parameter or class. `graph_summary` is the concise, database-owned
  explanation for a parameter's interactive graph popup; keep it short. The
  generator derives the survey definition catalogue directly from these fields.
- Treat a relationship record as a stated mathematical fact. Do not introduce
  inferred transitive relationships as new records merely to improve a graph.
- Keep names, definitions, relationships, values, and references aligned with
  the LaTeX counterpart whenever an edit changes mathematical content.
- The Hasse-like graph is deliberately conservative: only compatible linear
  relationship types are used to reduce the hierarchy. Nonlinear bounds and
  variant-specific relationships remain visible overlays.
- For an unlabeled compression claim, the decoder must take only the retained
  coordinate set: neither the omitted labels nor the original sample may affect
  its output. Replay all samples sharing a key against that one output. A
  labeled retain-all or cyclic-sign construction is not an unlabeled proof.
- Keep the declared ambient domain when studying antichain number. Constant
  coordinates can change its value; fixed-domain subclass monotonicity does
  not permit deleting newly constant coordinates. The canonical counterexamples
  are in survey `prop:antichain-monotonicity`; replay the cube formula and maps
  with `python3 sync/verify_noclashing_antichain_gap.py`.

## Local preview and deployment

Use the default `python3` (Python 3.13 on this workspace):

```bash
python3 ~/code/math_database/generate_website.py \
  --data_dir "$PWD/data" --output_dir "$PWD/docs" --deploy true
```

For interactive database editing instead, run:

```bash
python3 ~/code/math_database/server.py --data-dir "$PWD/data"
```

After changing `data/` or any renderer used by this site:

1. Regenerate `docs/` with the deployment command above.
2. Inspect the generated site, especially `docs/graphs/hasse.html` after graph
   changes.
3. Commit both source changes and generated `docs/` changes in this repository.
4. Push `main`; GitHub Pages deploys the tracked `/docs` folder.

If a change is made in `~/code/math_database`, commit and push that repository
separately as well; then regenerate this repository's `docs/` so the deployed
output includes it.

## Synchronization with LaTeX

Before changing mathematical content, inspect the corresponding material in
`~/latex/CombinatorialParameters`. After changing either repository, record or
perform the corresponding update in the other one. Until a dedicated sync
workflow exists, do not silently treat either representation as automatically
authoritative over the other.

`sync/latex_mapping.json` is the checked mapping from database parameters and
classes to LaTeX definition labels. Validate it after changing either inventory:

```bash
python3 sync/validate_latex_mapping.py \
  --data-dir data --latex-dir ~/latex/CombinatorialParameters

# `symbol` fields in both tables are bare TeX; renderers add delimiters.
python3 sync/validate_symbols.py --data-dir data

# Audits the proof/reference requirement for established values and
# relationships, plus each declared monotonicity classification.
python3 sync/audit_provenance.py --data-dir data

# Audits declared strict witnesses from endpoint values and declared unbounded
# witnesses from asymptotic value classes; legacy witnesses remain a review queue.
python3 sync/audit_witness_strength.py --data-dir data

# Regression: a growing additive difference must not be classified as an
# unbounded ratio; exact contradictions override prose certificates.
python3 -m unittest discover -s sync -p test_witness_ratio.py

# Screens every established direct relationship, including those omitted
# from the graph: missing witnesses, strict-to-unbounded leads, and reverse
# affine paths. Leads require endpoint proof and scope review before promotion.
python3 sync/audit_relationship_witnesses.py --data-dir data --check \
  --output sync/relationship_witness_queue.json

# Small-class counting and upper-bound witness-direction regression.
python3 sync/verify_dual_littlestone_bounds.py

# Independent teaching-order, no-clashing-map and degree computations behind
# the equality of the three positive projection closures.
python3 sync/verify_positive_projection_collapse.py

# Checks unambiguous established literal-integer benchmark values against
# direct linear and equality relationships. Formulae and scoped alternatives
# are deliberately skipped.
python3 sync/audit_benchmark_consistency.py \
  --data-dir data --fail-on-contradiction

# Replay the DB-owned stable labeled full-cube scheme on every partial sample
# through eight coordinates; reject the old symbolic values and strict witnesses.
python3 sync/verify_full_cube_labeled_compression.py

# Finds direct strict/unbounded witness edges which a transitive reduction
# would otherwise hide behind a witnessless path.  The graph preserves those
# as overlays.  Add --check-witness-bypasses to make unresolved localization
# (missing value evidence on every path edge) fail a review/CI run.
python3 sync/audit_hasse_edges.py --data-dir data

# Prioritizes cited primary sources whose companion literature packet is
# missing or incomplete.  Omit the limit option to list every gap.
python3 sync/audit_literature_packets.py \
  --data-dir data --latex-dir ~/latex/CombinatorialParameters --limit 25

# Rejects duplicate direct statements, which otherwise duplicate parameter-page
# entries and may obscure the intended canonical provenance record.
python3 sync/audit_relationship_duplicates.py --data-dir data --check

# Reconstructs the Hasse reduction and ranks witnessless, structurally
# important edges; use --all for the full research queue.
python3 sync/audit_hasse_edges.py --data-dir data

# Screens unrecorded directions against exact benchmark values. This is a
# research queue only: a listed direction is not a mathematical claim.
python3 sync/screen_benchmark_dominance.py --data-dir data

# Lists the current bottom-layer components and prioritizes pairs without a
# direct comparison; benchmark gaps are research leads, not inferred facts.
python3 sync/audit_leaf_layer.py --data-dir data

# Regression check for the graph's homogeneous transitive reduction.
python3 sync/verify_hasse_reduction.py

# Private-coordinate teaching/compression separation, including every small projection.
python3 sync/verify_private_coordinate_cube.py

# Independent finite lower proof for the projected-NCTD/compression gap.
python3 sync/verify_projected_nctd_compression_gap.py

# Hollow-star/proper-compression bounds and Three-Code correction regression.
python3 sync/verify_proper_compression_covc.py

# Unlabeled singleton decoders: improper size one, proper size two for n>=3.
# Reject omitted-sign access and exhaust all 81 proper size-one maps at n=3.
python3 sync/verify_singleton_unlabeled_compression.py

# Proper width-three CCT decoder: all partial samples, two independent replays.
# The certificate and product/counting proofs are database-owned; no solver needed.
python3 sync/verify_cct_compression.py

# Direct enumeration behind the repetition-free teaching separation value.
python3 sync/verify_repetitionfree_teaching.py

# Exact message-free labeled compression value on Warmuth's C5 class.
# Solver-free lower enumeration and full partial-sample upper replay.
python3 sync/verify_c5_labeled_compression.py

# Replay stable pair and ordinary five-cube decoder certificates, including
# the strict (not unbounded-ratio) separation from NCTD/stable compression.
python3 sync/verify_full_cube_labeled_compression.py

# Independently replay all projected-teaching plans for the finite OSC > RTD^p witness.
python3 sync/verify_chen_neighbor_puncture.py --data-dir data \
  --check-certificate sync/chen_neighbor_puncture_certificate.json.gz
```

Validate the monotonicity metadata after changing parameter properties or an
established equality relationship:

```bash
python3 sync/validate_monotonicity.py --data-dir data --check

# Reports every declared monotonicity flag without a proof or provenance entry.
python3 sync/audit_monotonicity_evidence.py --data-dir data

# This only backfills evidence forced by other declared properties; it does
# not infer foundational monotonicity claims.
python3 sync/backfill_monotonicity_evidence.py --data-dir data --write

# Verifies direct inequalities forced by registered max-over-subfamilies constructions.
python3 sync/validate_monotonicity_consequences.py --data-dir data --check
```

The database owns the structured catalogue and its LaTeX catalogue sources.
The LaTeX checkout consumes generated copies; do not edit its
`includes/generated/*`, `includes/defs.tex`, or `includes/cl_defs.tex` as
sources. Generate all catalogue outputs from here:

```bash
python3 sync/generate_latex_catalog.py \
  --data-dir data \
  --output ~/latex/CombinatorialParameters/includes/generated/def_table.tex

python3 sync/generate_latex_catalog.py \
  --data-dir data --section value-table \
  --output ~/latex/CombinatorialParameters/includes/generated/val_table.tex

python3 sync/generate_latex_catalog.py \
  --data-dir data --section value-proofs \
  --output ~/latex/CombinatorialParameters/includes/generated/value_proofs.tex

python3 sync/generate_latex_catalog.py \
  --data-dir data --section parameter-definitions \
  --output ~/latex/CombinatorialParameters/includes/generated/parameter_definitions.tex

python3 sync/generate_latex_catalog.py \
  --data-dir data --section class-definitions \
  --output ~/latex/CombinatorialParameters/includes/generated/class_definitions.tex

python3 sync/generate_latex_catalog.py \
  --data-dir data --section bibliography \
  --output ~/latex/CombinatorialParameters/includes/generated/references.bib
```

In CI or before committing the LaTeX repository, add `--check` to verify that
the generated file has not drifted.

The LaTeX survey continues to own only its narrative, proofs, and document
layout. Record any further shared section in `sync/ownership.json` before
moving it into this workflow.

The active research questions are tracked in the survey's
`conjectures/parameter_separations.md` and root `dashboard.json` / generated
`dashboard.html`. These are research state and navigation, not a second
catalogue of accepted facts. Follow its honest-conjecture-resolution and
conjecture-dashboard skills for campaign rounds; promote accepted facts here.

The cube--half-interval constrained-tree values have an independent exact
regression: `python3 sync/verify_cube_halfinterval_trees.py`. It enumerates
actual coordinate fibres on 84 product/block-size cases, including truncated
final blocks. The universal proofs live in the database value records, not in
the test output.

For the fixed-VC/unbounded-block separation, run
`python3 sync/verify_branching_batch_trees.py`. Its eight-family shattering
and path checks include six independently optimized small domains. Do not
describe the two larger structural checks as full depth optimizations.
The same verifier now checks the intersection-closed proper order scheme
and last-batch teaching lower bound. `--compression-only` skips depth
optimization; all 8059 realizable samples on the six small domains are
replayed, while the two larger cases check intersections and neighbours only.

The strict characteristic-dependent Yang witness is checked by
`python3 sync/verify_yang_characteristic_witness.py`. Its definition and
integral proof are database-owned; the verifier reuses the survey's exact
ambiguity calculator. For independent cube-interval verification and full
report reproduction, add
`--crosscheck-lattice ~/latex/YangDim/scripts/explore_yang_dimension_lattice.py --check-report sync/yang_characteristic_witness.json`.
The witness for the prime-indexed relationship is scoped to `p=2`; it is
strict, not unbounded.

The reverse characteristic-three witness is checked by
`python3 sync/verify_odd_torsion_yang.py --check-report sync/odd_torsion_yang.json`.
This verifies the integral source, actual top ambiguity boundary ranks, every
version-space size and the field-independent simplex-boundary conditioning.
It is not a full Betti census. Together the two classes refute both exact
dominations between characteristics two and three; do not label this as
unbounded incomparability.
