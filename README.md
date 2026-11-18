# Scientific news verification — implementation starter

Status: **preparation tools only**. No LLM generation/verifier adapter, real data download, final dataset, or experimental result is supplied. This is the first milestone for the defended research, not a completed research system.

## Start in Colab (recommended first session)
Open `notebooks/01_START_HERE.ipynb` in Colab. Mount Drive, point PROJECT to this extracted folder, inspect file paths, install audit dependencies, and run tests. Dataset files stay in your authorized Drive working folder. No token is required for local file inspection; use Colab Secrets for any later authenticated download.

## Windows setup alternative (Python 3.11+)
```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe run.py matrix --output artifacts/matrix.json
```
Do not type the PowerShell examples into a Python cell. In Colab use `%pip` and Python subprocess calls in the notebook.

## Step 1: schema (metadata-only output)
```bash
python run.py schema --input /YOUR/PATH/train.json --output artifacts/scinews_schema.json
python run.py schema --input /YOUR/PATH/valset.json --output artifacts/sciver_schema.json
```
JSON arrays stream through ijson; use `--prefix data.item` for a nested data array. JSONL files stream automatically. Three sampled records reveal examples, not the complete schema of every record.

## Step 2: confirm mappings, then audit
Copy the example mapping into ignored `private/`. Replace actual local paths/JSON pointers, explicitly validate SciVer label semantics, set `confirmed` to true only after inspecting correct fields.
```bash
python run.py audit --mapping private/scinews_mapping.json --output artifacts/scinews_audit
python run.py audit --mapping private/sciver_mapping.json --output artifacts/sciver_audit
```
Never map an abstract as full paper text without documenting that limitation. Scanning finds candidates and provisional groups; it does not establish paper identity, modality usability, near-duplicate absence or eligibility. Duplicate definitions differ from the older notebook, so counts require comparison rather than blind agreement.

## Step 3: review and split
Fill `templates/eligibility_review.csv` into private storage. Set eligible=yes only after every required paper/text/numerical/table/chart check. Assign a reviewed underlying-study ID; mark all previously inspected studies. One selected pair per study is required. Split tool trusts your human eligibility decision; it does not perform evidence review.
```bash
python run.py split --review private/eligibility_review.csv --output artifacts/split_plan.json
```
Default targets are 20/20/60; insufficient untouched studies fail rather than silently change the protocol. Known inspected studies are development-only. Split plans are provisional until final protocol review.

## Metrics demo — synthetic, not real findings
```bash
python run.py evaluate-sciver --gold examples/sciver_gold.SYNTHETIC.jsonl --predictions examples/sciver_predictions.SYNTHETIC.jsonl --output artifacts/SYNTHETIC_metrics.json
```
Real gold and predictions use separate JSONL files keyed by stable record_id. Gold labels never enter model inputs. ID mismatches/duplicates fail. Abstentions count against accuracy and recall. Technical failures are separately counted and included in the attempted denominator under an explicitly proposed policy; freeze the actual policy before testing. Record time/calls/memory in the run log later, not invented placeholders.

## What comes next
Follow `docs/IMPLEMENTATION_18_20.md`. Build a real development V0-E1 pilot after confirming actual schema, evidence and hardware. Select model dependencies on that pilot. Then integrate verifier/corrections and E2/E3; use the same frozen compatible verifier for separate SciVer assessment. Final test data must not select prompts/models/rules.

## Existing audit notebook
The previously supplied Full_Dataset_Eligibility_Audit notebook remains the bucket download/PDF inspection workflow. It is not bundled here because user-specific notebook content must be reviewed before committing. This starter performs no authenticated remote access.

## Storage / GitHub
See `docs/GITHUB.md`. Source, synthetic fixtures, blank templates and protocol decisions can be tracked. Keep raw data, PDFs, real evidence/annotations, secrets, model weights and local outputs out of git. No open-source licence has been imposed; choose the repository licence with your supervisor/institution.
