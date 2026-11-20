# Scope and evaluation preparation — development update

## Scope checking

`scope_guard_v1.check_scope_value` checks a single structured numeric assertion. It requires outcome, population, comparison, condition, measure and unit, exact source quotation references, an exact claim-value quotation, valid finite numbers and reviewed canonical scope mappings on both source and claim sides. Different or missing scope abstains. Matched reviewed scope with a wrong number refutes the numeric assertion; matched number supports only that assertion. It never grants whole-summary scientific approval.

This is NOT automatic semantic scope extraction. Source-string provenance does not prove that a canonical interpretation is scientifically right. The reviewed status is a recording mechanism, not automatic proof that a human review occurred. The guard is a new component API; it does not silently alter the old summarization runners or make their numerical policy complete.

`run_scope_preparation.py --project PROJECT --output NEW_DIRECTORY` prepares one operational contract DRAFT for the actual train:5 composite-primary-outcome relative risk. Exact source spans are taken from E1, source identity/correction provenance is checked, and review is pending. It is not a gold label or independent finding inventory and is not auto-loaded into model inputs. The canonical unit interpretation is explicitly noted for review. Do not mark pending contracts reviewed merely to obtain Supported.

## Eligibility queue

`run_evaluation_preparation.py queue --index FULL_RECORD_INDEX.csv --output NEW_DIRECTORY --limit 300`

Reads the existing audit index only. No large dataset re-download, paper download, model inference or news/paper text scan. Produces up to 300 TRAIN-source representatives, one per provisional group, skipping exact duplicate occurrences. These are review candidates, not 300 eligible studies. No new source-validation/test texts are inspected. Current known SciNews exposures train:0,2,3,4,5 are development-only at provisional group level. Supply `--additional-exposure PATH.json` as a list of record IDs for other known exposures. Exposure history is not assumed complete; all other rows remain unknown until checked.

Preserve eligibility_review.csv unchanged. Make a COPY named eligibility_review_completed.csv and fill:

- `study_id`: reviewed underlying-study identity, accounting for DOI versions and near duplicates.
- `selected_pair`, `eligible`: yes only after actual review.
- E1/E2/E3_readable: yes only when prose, tables and selected supported charts are readable and correctly associated.
- `important_numerical_findings`: evidence of meaningful numerical findings, not merely any digit.
- grouping/near-duplicate checks: actual review, not the provisional hash.
- `previously_inspected`: yes for exposed studies; no only after checking exposure history.
- reviewer, date, source_reference and notes: traceable review provenance and evidence locations. No fabricated annotations.

Cases with no suitable tables/charts can be ineligible for this planned three-condition design. Failed download alone is not scientific ineligibility; keep pending and record retrieval problems. Original source splits remain unchanged.

The index alone has no DOI, article content or eligibility proof. Queue generation does not complete screening. The first queue does not need to produce 100 eligible studies; add reviewed candidates if necessary.

## Grouped split and evaluation-only inventories

After actual eligibility and grouping review, run:

```
python run_evaluation_preparation.py split --review REVIEWED_COPY.csv --queue-manifest QUEUE_DIRECTORY/queue_manifest.json --output NEW_SPLIT_DIRECTORY
```

Preserves the original queue identity and known exposure fields. Requires one selected pair per reviewed underlying study and provisional group, completed eligibility checks, known exposure and reviewer provenance. Exactly 20 development / 20 validation / 60 test; insufficient reviewed untouched studies cause a hard stop, never a silent smaller sample. Inspected studies can only enter development. Excess inspected studies are excluded.

`evaluation_only/finding_inventory_templates.jsonl` is EMPTY templates, not completed inventories. Important source-based numerical findings must be independently written and checked without viewing system outputs, with source evidence IDs/quotes, importance rationale and first/second annotators. Do not supply this file to retrieval, writing or verification.

Second-annotator targets are 5 validation studies and 15 test studies (25% within each split). This is a planned review allocation, not proof of reviewer availability, inter-rater agreement or a literature-derived sample-size guarantee. Review completion fields start false. All templates/inventories must be validated and frozen before final system-output evaluation; this update does not certify or freeze incomplete inventories.

## Validation and limits

58 software tests passed: 43 existing and 15 new scope/preparation checks. Actual uploaded train:5 source contract preparation passed, and wrong-outcome and pending mappings abstained. A fully synthetic 100-study review-copy test produced exact splits, 100 empty inventory templates and 5+15 uncompleted second-review targets. No actual dataset split or study eligibility was manufactured.

No models run. No changes to historical outputs, datasets, old runners, prompts or tests. This adds preparation tools and a structured guard, not complete general verification, final test results, finding coverage or E3 competence.
