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

# Checks unambiguous established literal-integer benchmark values against
# direct linear and equality relationships. Formulae and scoped alternatives
# are deliberately skipped.
python3 sync/audit_benchmark_consistency.py \
  --data-dir data --fail-on-contradiction

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

# Regression check for the graph's homogeneous transitive reduction.
python3 sync/verify_hasse_reduction.py

# Direct enumeration behind the repetition-free teaching separation value.
python3 sync/verify_repetitionfree_teaching.py
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
