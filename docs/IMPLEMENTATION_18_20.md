# November 18–20, 2026: implementation sprint

These are work targets, not completed experiments. Gates take precedence over calendar dates.

## 18: foundation and evidence audit
1. Create/connect a private GitHub repo; use the source-only starter.
2. Run synthetic unit tests and metrics demo.
3. Run schema inspection on authorized SciNews/SciVer copies in Colab.
4. Confirm actual field mappings and SciVer raw label semantics.
5. Run full JSON audits, inspect duplicates and provisional cross-split groups.
6. Use the existing Full_Dataset_Eligibility_Audit notebook for bucket transfers/PDF checks.
7. Select 3–5 development-only pilot studies; mark every inspected study.
8. Human-review paper identity, numerical relevance, table/chart usability.
Deliverable: actual schema/audit reports + reviewed pilot manifest.
Gate: no guessed schema; no screening count described as final eligibility.

## 19: development-only evidence and V0 pilot
1. Draft annotation guidelines using development studies, not final test outputs.
2. Prepare pilot finding inventories with evidence locations and importance rationales.
3. Prepare E1/E2/E3 bundles with source-modality provenance.
4. Separate captions/table bodies/chart-derived records from E1.
5. Inspect available GPU, RAM, licence/access and budgets before selecting model candidates.
6. Implement claim extraction, retrieval and V0-E1 generation adapters.
7. Save actual candidate claims, evidence IDs and summaries; review errors.
Deliverable: real V0-E1 development run, if component access/resources permit.
Gate: do not use a mock generator as a scientific result; reference inventories never enter inference.

## 20: verifier integration and controlled pilot
1. Implement textual support + numerical checks; add compatible visual processing.
2. Implement Supported/Refuted/Insufficient Evidence and fixed correction bounds.
3. Add V1/V2/V3 with paired drafts and correct call accounting.
4. Exercise E2/E3 evidence boundaries on development cases.
5. Connect the same verifier procedure to a separate SciVer evaluation routine.
6. Exclude labels/perturbation metadata from inference. Log abstentions and failures.
7. Review pilot failures, reviewer availability and remaining protocol decisions.
Deliverable: integrated development pilot and honest remaining-work list.
Gate: if data/model stages are not ready, finish them rather than label the sprint complete.

## After the sprint
Complete eligibility, study grouping, annotations and reviewer checks. Select models/settings on development/validation only. Fix aggregation, statistical procedures, zero-claim handling, technical failure policy and timing boundaries. Freeze the protocol, then run the planned final studies/configurations. Never promise that final annotation and all 720 outcomes finish in three days.
