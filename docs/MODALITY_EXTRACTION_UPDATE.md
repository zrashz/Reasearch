# Separate-modality extraction development update

The observed joint multimodal extractor selected only two chart findings. This version extracts prose separately, then one chart finding in a second VLM call. Within the four-statement budget it reserves one available source-derived numeric comparison and one available chart finding. Unselected candidates and per-call raw responses are logged. This is a changed extraction policy and observation/call budget, not a matched-budget final benchmark. Same prose call is used across evidence conditions. No independent support is implied by inclusion.

Writer schema instructions now explicitly exclude echoed input keys. Strict parsing remains; malformed output is still a failure, never silently accepted. Writer length/quality improvement is not established.

Prose-reported percentage changes are compared with calculations from rounded cells before offering numerical candidates. ANI-1x 36% in prose versus 35% derived from rounded cells is unresolved source precision, not a proven paper error. Such a comparison is withheld and not silently rewritten. No inference values are hardcoded.

This remains a narrow conformer RMSD adapter and heuristic textual verifier. It does not complete general numerical verification, visual verification, independent evaluation or the research.
