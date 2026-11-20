# Numerical/writer development update

Adds a restricted RMSD percentage-comparison adapter for simple XML conformer-energy benchmark tables with explicitly linked scope prose. It derives method values from table cells and benchmark/range/reference from paper text. No hardcoded 2.07/2.54/23 values are used in inference. Original missing-scope claims remain insufficient; one source-assisted correction may add scope and evidence anchors, then the controller independently invokes the checker again. Wrong benchmark/range is not silently repaired. The broad “as well as” comparison remains unresolved.

This is not a general numerical/table/visual verifier. Only the documented canonical grammar is accepted. Numeric decisions use Decimal and explicit half-up rounding from reported table values. A Supported decision is about that restricted assertion; scientific_approval remains false and independent review is not established. E1 gains no tables and cannot use this adapter. Existing MAD adapter remains in place.

Writer instructions request source-supported detail for existing findings and target 95–115 words. Short outputs remain failures; no automatic regeneration, filler or post-verification padding. Source-derived optional numerical candidate hints are exposed only when the table and matching prose exist, and are logged. Prompt changes alter generation and must be treated as a new development version; prior runs are not replaced. Improvement is unproven until GPU execution and review.

Preserves the installed sentence-context module unchanged, requires its exact uploaded hash, and adds its regression controls. Runner identity now includes numerical and sentence-context source hashes.

Use install_numeric_writer_update.py PROJECT. It checks source identities, tests a temporary checkout before installing, backs up changes, and does not run models. Then run_numeric_writer_replay_v1.py on saved E3 extraction/evidence to test the numerical correction with zero model calls. This replay is not a V0–V3 run or new inference. Only after reviewing it, run one new GPU E3 case. Do not run the 15-paper batch yet.
