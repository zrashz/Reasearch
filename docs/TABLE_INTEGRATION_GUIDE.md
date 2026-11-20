# Table integration update — 19 November 2026

This adds one resumable, model-free development runner. It connects the existing latency binding adapter and explicit source-bound change arithmetic. It is NOT the final scientific verifier, a new model benchmark, or V0–V3 summarization integration.

## What it does

- Loads only prepared claim/evidence packets, never gold labels or assistant reviews.
- Validates rectangular cells and coordinate identities.
- Matches the existing restricted latency grammar and explicit change grammar.
- Preserves quotations, source cells, calculated differences and unresolved components.
- Saves each record separately; identical inputs and source code can resume without rewriting results.
- Rejects changed code/inputs on resume; use a new output directory for a changed experiment.
- Records malformed packets as technical failures; retains all records in counts.
- Gives no full scientific predictions. Operational outcome is Insufficient Evidence until scientific scope, complete decomposition and image/HTML correspondence are independently established. Partial arithmetic can be Supported or Refuted without becoming a whole-claim prediction.

## Install

Extract this ZIP into a temporary folder, then:

```python
subprocess.run([sys.executable, str(bundle / 'install_table_update.py'),
                '--project', str(PROJECT)], check=True)
```

The installer verifies the existing latency module against the uploaded source. It adds new files only; a different file at a destination is preserved and installation stops.

## Test

```python
subprocess.run([sys.executable, '-m', 'unittest', 'discover', '-s', 'tests', '-v'],
               cwd=PROJECT, check=True)
```

26 tests passed on the supplied code plus this update: 15 existing tests and 11 new integration tests. No models or private dataset files were available locally. Fixtures test source matching, arithmetic, withholding, blank values, ambiguous rows, coordinate validation, duplicate IDs, gold-label rejection and resume integrity. This is software verification, not empirical verifier accuracy.

## Run on your prepared packets

```python
prepared = PROJECT / 'private/structured_table_development/next_validation_cases_20261119T053405869660Z/prepared_tables_20261119T053727312131Z'
subprocess.run([sys.executable, 'run_table_development.py',
                '--inputs', str(prepared / 'evidence_packets.jsonl'),
                '--output', str(prepared / 'integrated_runner_v1')],
               cwd=PROJECT, check=True)
```

Expected from the previously displayed data: partial checks for val:451 and val:446; unresolved for val:45, val:438 and val:46. This expectation has not been run on the user's private files. All five operational decisions should remain Insufficient Evidence if their input structures match the prepared examples. Numerical contradiction candidates must not be reported as full verified scientific predictions.

## Remaining research work

General atomic claim extraction and coverage, scientific scope binding, reliable image/HTML correspondence, merged tables and visual extraction, NLI/numerical/visual arbitration, complete V0–V3 SciNews pipeline, eligible study selection and splits, independent findings inventories and reviewers, pre-test settings freeze, final experiments, metrics and error analysis remain unfinished. No further tiny-model retries are launched by this update. The CPU model extraction failures remain historical results.

## Existing limitations identified

The fraction guard checks only for the existence of a slash fraction, not whether extracted counts equal the written fraction. structured_numeric_v1 requires trusted, correctly scoped structured evidence. simple_table_v1 rejects merged cells; valid HTML may still omit important mathematical content. None of these old files is modified or promoted to a general verifier by this update.
