# GitHub workflow

Suggested name: scientific-news-verification. Start private. Keep original datasets/evidence/gold inventories/local outputs outside git; .gitignore protects common paths but is not a licence or secret scanner.

## First source-only upload (PowerShell or terminal)
Run from the extracted project folder, after connecting GitHub and choosing the actual repository URL:

```bash
git init -b main
git status --short
git add .gitignore .github README.md requirements.txt requirements-models.PENDING.txt run.py src tests configs docs templates examples notebooks
git diff --cached --stat
git commit -m "Add reproducible research preparation tools"
git remote add origin YOUR_ACTUAL_REPOSITORY_URL
git push -u origin main
```

The placeholder is not a real URL. If a remote repository already contains files, clone it first and copy source into that checkout instead. Do not force-push or overwrite existing history. Set your own git author identity if git requests it.

## Every work session
1. Pull current main, create a descriptive branch.
2. Make a small real change; run meaningful tests.
3. Add actual progress/decision notes and evidence hashes, not raw private data.
4. Review staged files; commit a truthful message; push branch and review a PR.
5. Tag a protocol freeze only when all final-test settings/references are complete.

Suggested milestones: M1-schema-audit; M2-eligibility-annotation; M3-v0-development; M4-verifier-integration; M5-validation-freeze; M6-final-experiments; M7-analysis.

Never fabricate daily commits or completed results. Store real logs in Drive; git records source/config revisions. A private repository does not automatically authorize restricted data redistribution. Review each notebook for stored tokens, text and gold outputs before committing it.
