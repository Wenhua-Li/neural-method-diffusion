# Data dictionary

All CSVs use UTF-8, a header row, and an empty cell for missing values. Boolean
fields are `True`/`False`. Identifiers must not be treated as arithmetic values.
`corpus_id` is the stable canonical join key across all released tables; it is
local to this frozen corpus, not a DOI. `analysis_papers.csv` has one record per
canonical research/review paper in the historical standard subset. Never infer
analytic inclusion solely from presence in that table.

`corpus_doi_list.csv` lists the DOI, venue abbreviation and year of every
canonical record in the full frozen corpus (121,332 rows, including the small
non-research portion outside `analysis_papers.csv`); it is the corpus-wide
citation inventory and carries no titles or abstracts.

`venue_key.csv` supplies the full names and group membership of all 27 target
venues. Abbreviations in figures join directly to this table; an export filename
is never used to infer an unmatched record's venue.

## Completed expert extension

`followup_role_labels.csv` (800 task annotations) and `followup_m1_labels.csv`
(200 annotations) contain investigator-confirmed manual expert labels. Together
they cover 991 distinct papers; nine papers occur in both tasks. Each task is
internally unique. Fields include `case_id`, `corpus_id`, `human_label`, unresolved
flag, task, sampled stratum, its population `N`, sample `n` and `pi=n/N`.
They contain no titles or abstracts. `human_followup_provenance.json` records
verification hashes and the limits of the supplied rater information.

Role strata are group × enrichment among recent non-hits, with 50 enriched and
150 ordinary papers per group. M1 strata are the recent core-conference/journal
populations excluding the original M1 gold, with 100 new units per group. Do not
pool old and new gold as a simple random sample. The analysis uses known old M1
reference units plus an estimate for their separately sampled complement.

`revision_human_role_*` are the primary expert-reference narrow-definition
estimates. `revision_human_wide_*` include substantive hybrids as sensitivity,
using a separate 24-cell family. `revision_human_m1_recent.csv` uses a separate
two-cell family for current core endpoints, not temporal changes. The earlier
`revision_calibrated_role_scenarios.csv` remains model-recall sensitivity and is
not the primary post-extension estimate. Inter-expert reliability is unmeasured.

## Paper-level data

| Fields | Meaning |
|---|---|
| `corpus_id` | Unique stable paper key, retained for papers without DOI. |
| `doi`, `doi_missing` | Original DOI if present and an explicit missingness flag. A DOI missing value is not a missing paper. |
| `oa_id`, `s2_id` | Optional OpenAlex and Semantic Scholar identifiers, without a guarantee of complete coverage. |
| `year`, `venue_abbr` | Indexed publication year and venue abbreviation. 2026 is incomplete and excluded by analysis eligibility flags. |
| `group`, `publication_type`, `target_venue` | Four prespecified venue groups, journal/conference type, and membership in the 27-venue set. `Unmapped` records remain visible but are not primary target-venue observations. |
| `ec_label` | Existing corpus EC relevance classification; sensitivity analyses use this separately from venue grouping. |
| `abstract_status` | `null`, `empty`, or `nonempty`; null and empty are both excluded from the revised primary text-analysis population. |
| `abstract_chars`, `abstract_truncated` | Original abstract length and whether it exceeds the historical 2,000-character prompt limit. These are text-free provenance fields, not the abstract itself. |
| `m1_eligible`, `m1_observed` | Revised target-venue, nonempty-abstract, 1990–2025 eligibility, and availability of a successful frozen M1 prediction among eligible papers. |
| `m1_label`, `m1_source` | Frozen primary contribution label and production source (`full`, `pilot`, `not_coded`). Labels may exist for historically coded papers now excluded; apply the eligibility/observed flag. |
| `llm_related` | Historical model flag for LLM involvement; not an independently human-verified classification of every paper. |
| `penetration_eligible`, `screen_hit` | Nonempty-abstract target-venue population through 2025, and title/abstract DL/LLM keyword-screen flag. |
| `extended_vocabulary` | Frozen vocabulary-enrichment flag used for non-hit recall strata. |
| `penetration_label` | `dl_native`, `neuroevolution`, `hybrid`, or `other` for adjudicated candidates. Missing non-hit labels are unmeasured, not human-confirmed negatives. |
| `era`, `period` | Historical sampling bins; always apply explicit year eligibility. The historical `period` upper bin can include 2026 before eligibility filtering. |
| `topic` | Fixed controlled-vocabulary application bucket. Generic missing/unclassified buckets are excluded from the topic common-support analysis. Topic balance does not establish causal exchangeability. |

M1 labels: `propose_new`, `improve`, `apply`, `hybrid`, `theory`, `benchmark`,
`review`, `other`. Coarse `method_dev = propose_new + improve + hybrid`.
The M1 `hybrid` label is a contribution category; the penetration-task `hybrid`
label specifically requires substantive EC and neural components. They are not
interchangeable variables.

## Sampling and human calibration

`sampling_m1.csv` contains the 1,998 historical pilot units and four model-label
columns. `era,N1,n1,pi1` identify the first-stage year-bin population, sample size,
and fraction. `candidate` identifies historical eligibility for the human-gold
pool (at least three successful model responses); `sampling_label` is the label
actually used to stratify that pool, including historical tie resolution.

`calibration_m1.csv` contains 300 human decisions, linked to that design.
`majority_label` preserves the saved pack label; `human_label` is the final expert
decision; `N2,n2,pi2` refer to the second-stage label stratum. `weight` is
`1/(pi1*pi2)` where the historical candidate design applies. `production_label`
is the final frozen production prediction, which is distinct from the pilot
MiniMax column. Three missing pilot labels therefore do not imply missing
production labels. A pilot unit excluded from gold candidacy has no positive
gold inclusion probability; see the methods note rather than extrapolating its
calibration weight.

`sampling_penetration.csv` contains the 2,000 first-stage validation units.
`label` is the frozen primary instrument prediction; `second_label` and
`masked_label` are the alternative-model and venue-masked predictions.
`stratum = group × label × period`, with population `N_h`, sampled `n_h` and
`pi1=n_h/N_h`. Its historical `weight` is first-stage inverse probability and
may have been rounded; calculations should use the integer sample sizes.

`calibration_penetration.csv` contains 300 human decisions. Its second stage
stratifies by `group × predicted label` across periods; `N2,n2,pi2` describe that
conditional draw. Here `weight=1/(pi1*pi2)` is the two-stage weight, not the
first-stage weight in the 2,000-paper table. `label` remains the machine label;
never substitute it for `human_label` when estimating calibration errors.

## Recall validation

`recall_validation.csv` preserves the 1,195 saved union members. `part` is the
historically retained stream assignment (`enriched` or `random`), `is_enriched`
is the historical enrichment stratum, and `extended_vocabulary` is the exported
paper-level enrichment flag. `in_random_non_enriched` identifies the recoverable
non-enriched random-stream members; it does not claim recovery of all 600
original random draws. `label` is the model adjudication of a screen non-hit,
not a human gold label. The analysis uses the enriched sample for the enriched
population and the non-enriched random members for the remaining population,
with year/group domain restrictions. The saved stream and repeated random-seed
limitations are disclosed in the methods note.

## Frozen outputs and metadata

`excluded_venue_provenance.csv` reports the stable IDs, year, indexed venue,
source provenance and abstract status of the 151 unmapped standard-subset
records; the file does not force these records back into a target venue.

`revision_data_manifest.json` contains exact current sample counts and exclusions;
use its values rather than older prose. `revision_numbers.json` adds analysis
metadata, common-support sample coverage and explicit uncertainty assumptions.

`revision_*.csv` files are deterministic outputs of `submission_analysis.py`:

| File family | Content |
|---|---|
| `roles_yearly`, `roles_windows`, `roles_venues`, `role_ratios` | Machine-observed counts and shares, narrow/wide role definitions, paper-weighted and venue-equal summaries. |
| `contribution_yearly`, `contribution_windows` | M1 counts/shares by year or five-year window and target/core/EC/historical scope. |
| `leave_one_out`, `topic_common_support`, `lag_holdout` | Venue omission, shared topic/year strata and time-held-out descriptive lag comparisons; no causal venue-policy inference. |
| `calibration`, `confusion_*`, `calibration_cells` | Human–instrument comparisons and per-cell population/sample/success counts used for finite-population uncertainty. |
| `calibrated_role_scenarios`, `calibrated_ratios` | Conditional working-design ranges combining human hit calibration with model-based non-hit recall. Not unconditional human-truth intervals. |
| `m1_difference_points` | Two-stage weighted human-minus-machine difference estimates; raw estimates and limitations are preserved, not clipped to manufacture plausible percentages. |
| `pilot_deltas`, `core_dl_topics` | Consistent-window pilot contribution deltas and per-year core-venue DL-native topic counts. |
| `abstract_coverage`, `missing_text_bounds` | Coverage counts and missing-text assignment sensitivity bounds. |

Every currently exported output is enumerated in `MANIFEST.json`, which is the
machine-readable source of truth if additional diagnostics are added. Percent
columns ending in `_pct` or `_pp` use percentage units; proportions such as
`pi1`/`pi2` are in [0,1]. Ratio columns are dimensionless. Counts are integer
unless labelled weighted, calibrated or estimated.
