# Implementation status — 19 November 2026

Evidence: uploaded 73-cell historical notebook and reported Colab outputs. The update's local tests are separate from the user's model runs.

## Completed development preparation
- SciNews audited: 41,872 source records; six exact duplicate occurrences; 66 provisional groups crossing source splits. Screening candidates: 36,965; not confirmed eligible studies. Group resolution still needed.
- SciVer validation: 1,000 prepared records, 504 single-item and 496 two-item; 1,661 referenced files read/parsed. Five ambiguous section references have assistant text-review overrides; visual and independent human review pending.
- Engineering image checks completed on single/two-image records; resized to 512 pixels. Not evaluated accuracy or final preprocessing.
- Five inspected SciNews development candidates saved; all development-exposed studies must remain out of final test, including study aliases/duplicates.
- train:3: 45 prose paragraphs and six full figure captions extracted. Summary/citation failures, unsupported virus claims and failed assisted correction retained. Supplementary tables do not automatically establish full eligibility.
- MiniLM retrieval tested on one development case. Whole-parent expansion changed the retrieval-context policy and must be recorded.
- Qwen writer and verifier diagnostics performed. Three hand-authored Qwen controls matched only one expected label. Focused DeBERTa NLI controls matched four expected labels with selected evidence; not a fair model comparison or benchmark accuracy.
- train:5: 71 prose candidates and four main tables; Table 3 correction linked and separately derived with arithmetic checks. E1/E2 candidate counts 71/75. Chart access/readability unresolved; eligibility unconfirmed.
- One generated numerical claim omitted explicit subgroup/counts. Extraction invented population and 38.2/100 counts. Guard withheld them; checker returned Insufficient Evidence.
- Reusable narrow numerical checker and lexical guard prepared. The workflow update consolidates status, source validation, provisional E1/E2 preparation, saved replay and optional live single-row diagnostic.

## Not completed
- General atomic claim extraction, provenance validation for every numeric/scope attribute, unit conversion, tolerances, risk-ratio/CI handling, conflict aggregation and calibrated thresholds.
- Full visual-verification/evidence integration and E3 preparation.
- Validated end-to-end scientific-news summaries across V0–V3/E1–E3; the assisted development correction is not a completed V2 experiment.
- Eligible independent study sample, reviewed group-level splits, independent finding inventories, second-annotator review and agreement analysis.
- Final model/prompt/rule freeze, 720 planned summary outcomes, fixed compatible SciVer assessment, correctness/coverage/abstention/cost analysis, final report.
- Remote GitHub upload/commit verification.

Immediate next work: obtain/review train:5 Figure 2 and source versions; broaden/check claim extraction on development cases; implement reusable main-pipeline orchestration with fair paired drafts. Keep final data reserved. Three-day targets are work plans, not completed experiments or guaranteed completion dates.
