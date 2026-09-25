# Companion code and text-free derived data

Public companion archive for the revised study of neural-network roles and
contribution patterns in 27 evolutionary-computation and neighbouring venues.
This is a venue-defined corpus, not a census of global evolutionary-computation
research. The current manuscript title is **Screening omissions and
methodological role reshape measured neural-method diffusion in evolutionary
computation** (set by the responsible author on 2026-09-25), also recorded in
`CITATION.cff`. This
package is hosted at https://github.com/Wenhua-Li/neural-method-diffusion;
no separate archival DOI has been assigned yet.

## Offline reproduction

Use Python 3.11.9 and the versions in `requirements.txt` (the tested environment).
Dependency installation is separate from reproduction and may require network
access. In an environment with these dependencies installed, run from this folder:

```console
python scripts/reproduce.py --data data --out reproduced
```

The command verifies SHA-256 hashes of the frozen package and input data, runs
the offline statistical analysis, generates four main and eight supplementary
figures, compares every generated statistical table with its frozen counterpart,
rebuilds ten LaTeX table fragments and numeric macros, compares them byte for
byte with the frozen versions, and writes `reproduced/reproduction_manifest.json`. It requires neither the
private database nor model credentials. Existing nonempty output directories are
rejected; choose a new output path for another run.

`MANIFEST.json` declares the actual export status and exact expected files.
An export marked `awaiting_current_plots` is a work-in-progress package and the
reproduction command refuses to describe it as complete. Reproduction logs are
saved even when an analysis or plotting step fails.

## Contents

- `data/analysis_papers.csv`: 118,750 canonical research/review records with stable
  corpus IDs, optional DOI/OpenAlex/Semantic Scholar IDs, eligibility flags and
  frozen categorical labels; no titles or abstracts. Target-venue and unmapped
  records remain explicitly distinguishable.
- `data/corpus_doi_list.csv`: DOI, venue and year for all 121,332 canonical corpus
  records, including the small non-research portion outside `analysis_papers.csv`;
  this is the corpus-wide citation inventory (no titles or abstracts).
- `data/sampling_*.csv`, `calibration_*.csv`, `recall_validation.csv`: the historical
  sampling design, inclusion probabilities, human/model label pairs and recall
  samples. Read the design limitations before interpreting uncertainty.
- `data/revision_*.csv` and `revision_numbers.json`: frozen analysis outputs;
  precise source filenames and hashes are listed in `MANIFEST.json`.
- `scripts/submission_analysis.py`, `submission_followup.py`, `submission_plots.py`, `submission_tables.py`,
  `style.py`: public-data analysis, plotting and LaTeX table/macro generation.
- `data/latex/`: the ten frozen table fragments and `numbers.tex`/`numbers.json`;
  reproduced versions are written to `reproduced/latex/`.
- `instrument/`: exact historical prompts and response parsers extracted without
  executing the original model clients; these document measurement provenance.
- `figures/`: frozen PNGs and vector PDFs (`figures/pdf/`) for the revised set.
- `DATA_DICTIONARY.md`, `METHODS_REPRODUCTION.md`: field definitions, limitations,
  and the boundary between frozen-result reproduction and rerunning models.

`export_current.py` is a maintainer-only packaging tool. It needs the private
working-tree layout but does not query its database or call models. It is not
part of the reviewer's reproduction command. The superseded scripts and figures
are retained in the project's pre-revision archive, outside this submission
package; they are not alternative scientific results in this release.

## Interpretation and data access

The role label `dl_native` excludes substantive EC–neural combinations by
definition. `neuroevolution` and `hybrid` are separate categories. A low
`dl_native` share is not a measurement of all neural-network uptake. M1
`method_dev` combines `propose_new`, `improve`, and `hybrid`; it measures reported
contribution orientation, not verified originality, quality or field health.

The completed expert extension contains 800 role and 200 contribution annotations
on 991 distinct papers; its public derived files omit all source text. Primary
role estimates now use human references for hits and non-hits. Historical
model-recall scenarios remain separately labelled sensitivity results.
Reported simultaneous ranges are conditional on the stated sampling design;
historical seed reuse and unmeasured inter-expert variation prevent unconditional claims
of design-exact human-truth coverage. See `METHODS_REPRODUCTION.md`.

Raw bibliographic records, titles and abstracts are not redistributed. The
corpus combines subscription Compendex exports with supplemental sources and
historical processing; an Engineering Village subscription alone does not
guarantee reconstruction of this exact frozen database. The public stable IDs
support cross-table tracing even when an external identifier is missing.

## Licences

Code: [MIT](LICENSE). Derived categorical records and aggregates:
[Creative Commons Attribution 4.0 International](https://creativecommons.org/licenses/by/4.0/).
These licences do not relicense the providers' original records or abstracts.
No manuscript acceptance or model-output determinism is implied.
