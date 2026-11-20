# SciNews stage integration — development only

## Validated on the supplied files

All ten supplied file hashes match the export manifest. The real-data offline audit verified 71 E1 prose records, 75 E2 records, 76 E3 records, unchanged shared prefixes, original/correction identities and corrected Table 3, table XML parsing, chart SHA-256 and the news-paper DOI. A copy of the inputs was used to confirm that E1 visual payload contamination, E2 chart contamination and a changed E3 image hash are rejected. Original input files were not modified. These checks do not establish scientific eligibility or paragraph-level semantic extraction correctness.

## Delivered behavior

- `run_scinews_development.py` defaults to an audit/12-configuration plan. It performs no model inference.
- `--live --condition E1` or E2 runs the optional CPU development backend.
- E3 live execution is explicitly blocked because a reliable visual adapter has not been established. Chart captions alone must not stand in for visual interpretation.
- V0/V2 share a raw draft; V1/V3 share the draft generated from prechecked findings.
- Each enabled checking stage permits one correction per statement followed by one recheck. Unresolved statements are withheld; empty and short summaries remain failures/abstentions, never padded.
- All citations must refer to evidence in the current condition's selected context. Each result includes structural checks; anchors are identifiers, not proof of support.
- Model steps are journaled individually, including failed raw responses, runtime, calls and token counts. Resume checks inputs, code, backend and environment identity. Failed events are preserved; changed prompts/settings require a new output directory.
- No assistant reviews, SciVer gold labels or independent finding inventories are loaded.

## Optional backend: important limits

Pinned Qwen2.5-1.5B extraction/writing and pinned DeBERTa NLI are supplied as an engineering backend, not selected final models. No live model inference was performed here. Model loading/dependencies must be checked in Colab. This update does not install or downgrade packages.

The retriever is explicitly lexical and limited to six whole records/18,000 characters. It is not the final embedding retriever. Context exclusions are logged. Long NLI inputs abstain instead of silently truncating.

The NLI threshold 0.9 is an uncalibrated development setting. All cited prose premises must individually pass it; contradiction scores alone do not produce Refuted. Numerical statements abstain because the narrow existing percentage/latency adapters do not cover generated scientific prose generally. Table and visual verification also abstain. Unsupported numerical/visual claims are not “fixed” by deleting essential conditions; unavailable corrections return null without a model call. NLI output does not independently establish scientific scope or atomic completeness. Every live outcome explicitly has automatic_scientific_approval=false.

This backend will over-abstain and may fail JSON generation. Its purpose is validating actual extraction/writing/stage wiring, preserving real failures, not achieving a publishable score. The old numerical adapters remain unchanged and are not falsely promoted to full free-text verification.

## Install and audit

Extract the update ZIP into a temporary folder and execute `install_scinews_update.py --project PROJECT`. It checks old source hashes, adds only new files and rejects conflicting destinations.

```python
subprocess.run([sys.executable, '-m', 'unittest', 'discover', '-s', 'tests', '-v'], cwd=PROJECT, check=True)
subprocess.run([sys.executable, 'run_scinews_development.py', '--project', str(PROJECT), '--output', str(PROJECT / 'private/scinews_stage_runs/audit_v1')], cwd=PROJECT, check=True)
```

36 tests passed locally on supplied source plus both integration updates (26 previous + 10 stage tests). Stage tests use a clearly synthetic backend and demonstrate routing/correction constraints only. The actual-file audit ran with zero models. Neither result is final scientific evaluation.

## Run one live development condition

```python
subprocess.run([sys.executable, 'run_scinews_development.py', '--project', str(PROJECT), '--output', str(PROJECT / 'private/scinews_stage_runs/train5_E1_live_v1'), '--live', '--condition', 'E1'], cwd=PROJECT, check=True)
```

CPU execution may take substantial time. Release older model variables or restart the runtime to reclaim RAM before launching this subprocess; Drive results persist. A subprocess loads its own models and cannot reuse notebook RAM models. Do not reinstall packages automatically. If model imports or loading fail, inspect that error before rerunning anything. If a generation stage fails, its saved event remains failed; inspect raw output, never silently turn it into Insufficient Evidence.

Review `V0.json`–`V3.json`, `events/`, `backend.json` and `run_summary.json`. Missing configuration files mean the run failed before producing them, not missing/filtered study outcomes. Completed draft outputs remain available even if a later stage fails. E2 uses a different output directory. Do not use these inspected development studies as final test data.

## Remaining work

Reliable general atomic extraction, calibrated scope-sensitive verification, source-bound numerical adapters, a working visual backend, final embedding retrieval, eligible study selection and grouped splits, independent finding inventories, second annotation, settings freeze and final paired experiments remain incomplete. This update provides real stage orchestration and auditability; it does not complete the defended experiment or independently certify generated summaries.
