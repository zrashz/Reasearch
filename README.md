# Evidence-Grounded Scientific News Summarization

Development prototype for scientific summarization using paper prose,
tables and selected chart images, with verification before and/or after
summary generation.

## Current status

The project includes evidence preparation, structured numerical checks,
sentence-level textual entailment with context checks, GPU generation,
correction handling, and V0–V3 development execution.

This is not a completed or independently validated research system.
Software tests do not establish scientific accuracy.

## Evidence conditions

| Condition | Evidence |
|---|---|
| E1 | Paper prose |
| E2 | The same prose plus tables |
| E3 | The same prose and tables plus selected chart evidence |

Evidence packets preserve source identifiers and provenance.
Availability of chart evidence does not guarantee its use by the writer.

## Verification configurations

| Configuration | Verification |
|---|---|
| V0 | No verification |
| V1 | Before generation |
| V2 | After generation |
| V3 | Before and after generation |

The stage controller logs checks, corrections, withheld claims and failures.
Invalid model-generated approval flags are not accepted as verifier results.

## Implemented components

- Dataset schema inspection, provisional grouping and eligibility preparation.
- Public full-text screening and evidence-packet preparation.
- Structured value, difference, ratio and percentage checks.
- Restricted source-specific numerical adapters.
- Sentence selection and textual entailment with context checks.
- Multimodal extraction and summary generation.
- Strict structured-output parsing and correction handling.
- Saved events, source/code hashes and development diagnostics.

## Repository layout

- `src/researchqa/`: implementation modules.
- Root Python scripts: command-line runners.
- `tests/`: software tests and required fixtures.
- `notebooks/`: Colab workflows.
- `docs/`: supporting documentation.
- `configs/`, `templates/`, `examples/`: preparation resources.
- `private/`, `artifacts/`: local data/results; exclude from Git.

## Colab workflow

For the current GPU development workflow, open
`notebooks/04_GPU_DEVELOPMENT.ipynb`.

Mount the authorized Drive project and verify installed code before running.
Select a T4 runtime and confirm CUDA availability for multimodal generation.
Do not reinstall old update packages over the current code.

Notebook 01 documents the original preparation stage. Notebooks 02 and 03
provide later workflows; inspect their instructions before execution.

The working Drive project is normally:
`/content/drive/MyDrive/scientific-news-verification`.

Historical evidence packets can contain absolute Drive image paths.
A fresh clone does not include private datasets, prepared evidence or models.

## Environment

`requirements.txt` contains the original audit dependency.
It is not a complete dependency specification for the current model pipeline.

A previous working Colab GPU runtime reported:
- Python 3.13.18
- PyTorch 2.14.1+cu130
- Transformers 5.22.1
- NVIDIA Tesla T4

These are observed versions, not a portable installation guarantee.
The current CPU runtime is a separate environment.
See `docs/ENVIRONMENT_STATUS.md`.

## Software tests

With the necessary dependencies already installed, run from the project root:

```bash
python -m unittest discover -s tests -v
```
