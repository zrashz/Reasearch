# Sentence/context development update

Preserves writer-key alias and fail-closed correction fixes from the uploaded source.
Selects one source sentence by lexical claim coverage before NLI scoring, preserving exact character offsets. Checks the selected sentence, neighboring context and full cited paragraph. Threshold remains 0.9 and uncalibrated. Strong contextual contradiction blocks provisional support; detected contextual caution requires contextual entailment too. No context is silently truncated.

A narrow important-role background filter plus clearer extraction instructions reduces the observed background-only selection. This is not complete finding classification.

Removes the previous exact-source shortcut so copied claims cannot bypass context checks. General numerical claims remain withheld unless the existing source-specific adapter handles them. No gold labels, past reviews, or diagnostic scores are used as inference inputs.

Offline tests use mocked scores to test software routing, not actual NLI accuracy. Sentence splitting, lexical selection, qualifier heuristics and NLI remain imperfect; no calibrated scope verification or scientific approval is claimed. Full-paragraph neutrality is not a contradiction. This policy change must be evaluated on development data and frozen before held-out evaluation.

Run install_sentence_update.py PROJECT; then the existing single-paper GPU cell in a new timestamp directory. Do not overwrite previous results or start the 15-paper batch before inspecting the new outputs. No GPU inference was performed during packaging.
