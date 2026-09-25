# Reproduction boundary and measurement provenance

## What the default command reproduces

The default offline command recomputes the revised statistical tables and four
main/eight supplementary figures from the frozen categorical records and
validation labels. It verifies input hashes and compares all exported computed
CSV/JSON outputs. PNG hashes are also reported; font or plotting-library
differences may change rendering without changing numeric results. PDF hashes
are recorded but are not required to match because metadata can contain build
timestamps. The final success/failure record is `reproduction_manifest.json`.

The archived derived-data population contains 118,750 canonical
research/review papers, including explicitly marked unmapped records. The
revised primary text-analysis universe is the 27 target venues with nonempty
abstracts and the stated year range. Read `revision_data_manifest.json` for
current exact counts; the older 99,322 historical pool used a non-NULL test,
which also admitted empty strings. Historical and revised scopes are retained
as different variables, not silently overwritten.

## What it does not reproduce

Rebuilding the source corpus requires licensed Compendex exports, supplemental
DBLP/citation-source records and the original cleaning/canonicalization history.
Raw titles, abstracts and subscription exports are not in this archive. External
indexes also change. The DOI/OpenAlex/S2 identifiers and corpus keys support
paper-level tracing, not a guarantee that a new source download will reconstruct
the exact historical database.

The default command does not call an LLM. Re-running commercial instruments
requires the user's own lawfully obtained text and service access. Even an
identical provider model alias and prompt need not produce identical outputs
at a later date. Frozen predictions are therefore the reproducibility target
for this release; no commercial-model rerun is necessary to review the results.

## Frozen instruments

`instrument/m1_prompt.txt` and `penetration_prompt.txt` are AST-extracted exact
historical template literals from the actual coding scripts, including the
escaped JSON braces required by Python `.format`. The parsers contain the
historical JSON extraction and validation code. They have no model client,
database import, user-config lookup or network side effect. Extraction source
hashes are recorded in `prompt_provenance.json`.

Primary instrument: provider model alias MiniMax-M3. Historical M1 output cap:
4,096 tokens; dedicated role adjudication cap: 256 tokens. Coding passed venue,
year, title and the first 2,000 abstract characters. Provider-default decoding
parameters were used unless explicitly recorded for the pilot alternative
model; the provider's undisclosed defaults and immutable model revision are
not recoverable from these files. The instrument templates include substantive
framing of DL-native as outside-in penetration; the revised paper treats these
as operational role categories and reports wider definitions separately.

`provider_config.example.json` is a nonexecuting schema example for documenting
a possible future rerun. It contains no credential, real endpoint or runnable
request. Supply credentials yourself in a separately implemented client; do not
place them in this package. Re-running coding is not an instruction performed
by `reproduce.py`.

## Human calibration and uncertainty

The two final 300-paper gold sets are expert-reviewed decisions. M1's historical
pilot comparison has 297 complete MiniMax pairs, while final production labels
permit a different 300-pair comparison. These are distinct evaluation objects.
The historical majority label resolved ties in model iteration order; the
paper must not claim tied samples were excluded when presenting all-300
metrics. A majority vote is an instrument comparator, not a replacement gold
standard.

Gold sampling was not simple random sampling of the full corpus. M1 had an
era-stratified pilot and contribution-label-stratified gold draw; the role task
had group/label/period first-stage strata and group/label second-stage strata.
Use the released integer stratum counts and two inclusion probabilities, not
one overall kappa or a first-stage weight alone. One M1 pilot unit was excluded
from candidacy because fewer than three models succeeded. It is outside the
two main endpoint windows; its absence still limits whole-period calibration.

The historical sampler repeatedly used the same random seed across strata and
stages. Conditional SRS working-design inference is therefore stated as an
assumption, not an exact property of the realized joint randomization. Sparse
gold cells and zero observed errors do not establish zero population error.
The revised calculation uses hypergeometric inversion and a declared
Bonferroni family for conservative simultaneous working-design ranges; zero
sample cells retain the full feasible range.

The historical non-hit recall sample has model labels. Its two streams were
deduplicated in an order-dependent union; the archive preserves that assignment
and recoverable non-enriched random members. These model-recall scenarios remain
available as historical sensitivity results, not the current primary calibration.

The completed extension supplies 800 expert-labelled recent non-hits and 200
expert-labelled recent core M1 papers, on 991 distinct papers across the two tasks.
The investigators confirm manual expert labeling; identities, exact dates and
independent inter-rater replication were not supplied. The sampling files omit
source text but preserve IDs, N/n and inclusion probabilities. Labels from the
new role sample replace model labels in primary non-hit estimation, while old
human hit calibration retains its historical conditional-SRS assumptions.
Each role definition has a separate 24-cell simultaneous family. Narrow ratio
lower limits exceed one but remain below three. Wide-definition coverage is
not joint with narrow-definition coverage or with the new two-cell M1 family.

The 200 new M1 references are drawn from the complement of the old gold in each
recent core population. The old reference units in that population are treated
as known; the new SRS estimates the complement. This avoids double weighting
and does not invent an interval for a long-term human-labelled trend.

## Comparability and interpretation

Venue-equal, same-window, omission, topic-support and held-out lag analyses are
descriptive robustness checks. SSCI has only 2021–2023 data within the nominal
2021–2025 window, so an explicit 2021–2023 comparison is provided. Topic common
support reports covered sample sizes and excludes unmatched topics; it cannot
separate editorial policy from all differences in the journal populations.
Contribution shares measure abstract-reported methodological orientation. The
superseded name-survival/benchmark proxies do not establish independent reuse,
algorithm quality or continued field generativity and are not default outputs.

## Maintainer export

After completing analysis and plots in the private project, run:

```console
python release/scripts/export_current.py --project PROJECT_ROOT --figure-dir PROJECT_ROOT/results/figures
```

The allowlist copies text-free data, current analysis/plotting/style scripts,
instrument templates/parsers and the 12 current figure stems. It rejects
title/abstract/raw-text/credential columns and removes legacy active scripts
whose old paths depended on the private working tree. The superseded package
is retained in the project's pre-revision ZIP, not mixed with current public
results. A fully exported manifest is necessary but not sufficient: run the
default command in an isolated copy and inspect its final verification record.
