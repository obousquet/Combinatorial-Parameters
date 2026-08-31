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
```

The database owns the structured parameter catalogue. Generate the LaTeX
parameter and value-table includes from it rather than editing those generated
files:

```bash
python3 sync/generate_latex_catalog.py \
  --data-dir data \
  --output ~/latex/CombinatorialParameters/includes/generated/def_table.tex

python3 sync/generate_latex_catalog.py \
  --data-dir data --section value-table \
  --output ~/latex/CombinatorialParameters/includes/generated/val_table.tex
```

In CI or before committing the LaTeX repository, add `--check` to verify that
the generated file has not drifted.

The LaTeX survey continues to own its narrative, proofs, and bibliography.
Do not extend generation to another shared section until its ownership is first
recorded in `sync/ownership.json`.
