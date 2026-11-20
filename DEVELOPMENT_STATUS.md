# Development status

Updated: 20 November 2026.

## Completed development work

- E1 prose, E2 prose-plus-tables and E3 chart evidence preparation.
- Connected V0–V3 generation and verification stages.
- Structured numerical checks and restricted source-specific adapters.
- Sentence-level textual entailment with context checks.
- Strict response parsing and invalid correction handling.
- Reported offline software tests: 137 passed.
- Input audit completed for train:1074 and train:13803.
- Assistant review of their tables, captions and chart images saved separately
  from model inputs.

## Latest reported live result

The ANI train:14460 E3 run completed V0–V3 without a runtime error.
All four summaries were identical at 79 words, below the required 80–120.
The final summaries did not cite chart evidence.
This does not demonstrate improved factual accuracy or chart reasoning.

## Current blocker

Colab GPU usage limits prevented further GPU allocation.
Live generation for train:1074 and train:13803 remains pending.

## Remaining work

- Run the two selected development cases.
- Review length, factual support, omissions and modality contribution.
- Improve general behaviour beyond the inspected ANI case.
- Validate dependencies in a fresh environment.
- Complete eligibility and independent review.
- Calibrate and freeze the configuration before final held-out evaluation.

Software test success is not scientific validation.
Final research evaluation is incomplete.
