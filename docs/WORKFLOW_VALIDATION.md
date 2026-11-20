# Validation and limitations

- Nine standard-library unit/integration tests pass locally: raw extraction preservation; observed missing-field abstention; explicit-form recognition; numerical versus scope mismatch; source hash refusal; altered derived-row refusal even with updated hash; identical E1 prose in E2; strict JSON parsing; append-only run directories and exclusive writes.
- Original six starter tests are checked alongside the update in the installation smoke test.
- Python source and notebook cell syntax checked. Clean notebook contains no execution outputs or credentials. The original 73-cell upload is not modified or included; only per-cell hashes/metadata are supplied in the inventory.
- No real model inference, network source acquisition, Google Drive access, or GPU inference has been rerun in the local verification environment. Live Qwen adapter follows the previously working API but still needs one fresh Colab run.
- Existing research data stay external; missing paths fail clearly. Figure access and annotations remain pending. Software tests do not establish scientific validity.
- Source-only installer tested against a disposable copy of the original starter; rerunning it is idempotent and preserves original run.py and the historical notebook.
