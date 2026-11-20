# Source-bound development fix v2

The failed v1 run is preserved. Its extractor copied a prompt placeholder; the v1 schema gate accepted it. Lexical retrieval chose background studies, not the present trial's main results. The writer returned uncited Markdown rather than JSON and mixed prior-study findings with the current study. Do not repair that content into accepted scientific output.

Changes: current-study Abstract Results are prioritized over background lexical matches; candidate statements are exact spans from explicitly labelled Results/Conclusions; generated template placeholders cannot become candidates. The candidate stage uses zero model calls. Writing receives only those source quotations and uses plain anchored text instead of JSON. Strict parsing rejects headings, missing/unknown evidence IDs and uncited trailing text. Syntax acceptance is not factual verification. Sentence selection is heuristic and extractive, not validated atomic claim extraction, and it changes the experimental procedure: do not compare v1/v2 as if only formatting changed.

The existing numerical-abstention and conservative NLI policies remain unchanged. E3 remains blocked. Settings are development settings, not frozen final parameters. No benchmark accuracy or finding coverage is established.

Install new files only using install_source_fix_v2.py --project PROJECT. Old files/results are untouched. Conflicting destinations are rejected. Dependencies must match the supplied installed v1 code.

Offline preparation (zero models):
python run_scinews_development_v2.py --project PROJECT --output PROJECT/private/scinews_stage_runs/source_gate_v2

Outputs: scinews_audit_plan.json and source_candidates_v2.json. On the actual supplied train:5 files, four source quotations were selected from the main Abstract Results, preserving the no-difference caesarean statement and the primary/secondary outcome distinction. All ten source-file hashes were already verified. 43 software tests pass (36 previous + 7 new), including prompt-echo rejection, result-prioritized retrieval, exact source spans, background-only rejection and strict anchored parsing. No live v2 generation has been run here.

Live E1 command, after offline preparation and reclaiming notebook model RAM:
python -u run_scinews_development_v2.py --project PROJECT --output PROJECT/private/scinews_stage_runs/train5_E1_live_v2 --live --condition E1

Never reuse train5_E1_live_v1. Save and inspect any v2 failure; do not retry blindly. Correctly cited prose can still be scientifically wrong, and the conservative verifier can over-abstain. Source-span candidates are pipeline inputs, never independent evaluation inventories.
