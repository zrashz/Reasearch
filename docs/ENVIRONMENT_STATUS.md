# Environment status

## Dependency coverage

requirements.txt contains the original audit dependency, ijson==3.3.0.
It is not a full dependency specification for the model pipeline.
requirements-models.PENDING.txt is documentation, not a pip installation file.

## Previously observed working GPU environment

- Python 3.13.18
- PyTorch 2.14.1+cu130
- Transformers 5.22.1
- NVIDIA Tesla T4

These are reported environment observations, not a validated portable lock file.

## Development models

- Generation: Qwen/Qwen2.5-VL-3B-Instruct.
- Textual verification: cross-encoder/nli-deberta-v3-small.

Use the exact resolved revisions saved in the project's model-pin records.
Model weights and private pin records are not bundled in this documentation.

## Current CPU runtime

The current runtime reported PyTorch 2.14.1+cpu and CUDA unavailable.
Colab displayed a GPU usage-limit message.
Reinstalling PyTorch does not allocate GPU hardware.

## Remaining environment work

Inspect active imports, consolidate dependencies, retain exact versions,
and test a fresh installation. Document CPU and GPU environments separately.
Do not claim one-click reproducibility before validating it.
