# Resume and run development work

Keep `01_START_HERE.ipynb` as the historical notebook. This update does not modify it, download datasets, recreate annotations, or claim completed research experiments.

## Install once
1. Save and download your current notebook as a backup.
2. Extract `Scientific_News_Workflow_Update.zip` separately into `MyDrive/scientific_news_workflow_update`.
3. In Colab mount Drive, then run:

```python
from google.colab import drive
drive.mount('/content/drive')
import subprocess, sys
subprocess.run([
    sys.executable,
    '/content/drive/MyDrive/scientific_news_workflow_update/install_update.py',
    '--project', '/content/drive/MyDrive/scientific-news-verification'
], check=True)
```

The installer verifies bundled hashes, copies only listed source/notebook/document files, and backs up changed existing files under ignored `private/update_backups`. It does not copy its package `__init__.py` over your project or change original starter `run.py`. It never pushes to GitHub.

Open the installed `notebooks/02_RESUME_AND_RUN.ipynb` and use that notebook for the next session.

## Commands
Run from the existing project directory, or supply `--project`:

```bash
python research_workflow.py status
python research_workflow.py replay-saved
python research_workflow.py prepare-evidence
```

- **status:** checks paths, package versions and GPU tools without importing model libraries. FOUND is not proof of scientific completion.
- **replay-saved:** verifies source/correction identities and hashes, replays the saved train:5 claim extraction through the lexical guard and percentage checker. No new inference; expected observed result is Insufficient Evidence for missing fields.
- **prepare-evidence:** rebuilds provisional E1/E2 files from saved reviewed sources. Identical prose is shared; corrected Table 3 replaces only that table in E2. Captions and footnotes remain in table XML. E3 and full eligibility stay pending.

Every non-status command creates a unique `private/workflow_runs/<UTC timestamp>_<id>` directory with source hashes, result or failure diagnostics. Older artifacts remain unchanged. A failure is not silently mapped to a scientific claim label.

## Optional fresh live row pilot
This command performs TWO new Qwen calls: one source-grounded claim generation, then claim-only extraction, followed by guard/checking. It is a narrow single-row diagnostic; not a V0–V3 summary experiment, visual test or SciVer benchmark.

Use a fresh Colab session (mount Drive again) so old RAM-resident models do not compete with a new process. Existing working dependencies need no reinstall. If model packages are missing, use the optional compatibility profile in an isolated environment; installing it globally downgrades HF Hub and can conflict with Gradio/Diffusers.

```bash
python research_workflow.py live-row-pilot
```

The fixed development Qwen revision is recorded in code. This new wrapper uses a 256-token cap and its own prompts; do not represent it as an exact reproduction of earlier notebook calls. Draft and extraction outputs are saved immediately. The extractor receives only claim text, canonical schema definitions, and no source numbers/gold labels. The final checker separately receives source evidence.

## Numerical validity limits
The guard only recognizes narrow explicit population wording and slash-fraction presence. It DOES NOT prove extracted counts correspond to that fraction, percentages match literal mentions, group assignment is correct, or multi-part claims are atomic. The numerical evidence adapter is specifically reviewed train:5 Table 3 NICU-duration evidence. Reported percentages are compared exactly; this is not a generic tolerance or unit-conversion implementation. All wrapper outputs set automatic_approval=false. An internal Supported label is not sufficient to accept a research summary.

## Dependencies and tests
Status, replay and evidence preparation require only Python standard library. Live inference additionally needs PyTorch, Transformers and compatible Hub/tokenizers packages. The optional pinned profile is NOT a final experimental freeze.

```bash
python -m unittest discover -s tests -p test_workflow_update.py -v
```

Nine tests are software checks on small fixtures, not scientific accuracy results. The uploaded Colab datasets/model runs have not been rerun by this package's author environment.

## GitHub
Repository: https://github.com/zrashz/Reasearch

Review and upload these source paths after installation:
- research_workflow.py
- src/researchqa/workflow.py
- src/researchqa/numerical.py
- src/researchqa/extraction_guard.py
- notebooks/02_RESUME_AND_RUN.ipynb (clear outputs before committing)
- tests/test_workflow_update.py
- docs/WORKFLOW_GUIDE.md, docs/IMPLEMENTATION_STATUS_2026_11_19.md, docs/WORKFLOW_VALIDATION.md, docs/notebook_inventory.json
- requirements-workflow-optional.txt

Keep private/, datasets, source papers, actual model outputs, secrets, backups and ZIPs out of Git. Do not force-push. Keep the original notebook locally; it contains source/evidence outputs and is not included in this source-only update. No GitHub upload or commit is claimed by this deliverable.
