# B0/B1 comparison on identical submitted Lean files

B0: Lean process exit code only. B1: additional checks on externally requested theorem, controlled integrity flag, and Lean `#print axioms` output. Same Lean source is submitted to both B0 and B1. The test fixture contains 12 cases derived from the original audit script.

## Execute

Create a GitHub repository, upload `compare.py`, `lean-toolchain`, and `.github/workflows/compare.yml` preserving paths. In Actions choose **B0 vs B1 comparison → Run workflow**. Download the `b0-b1-results` artifact. It includes `comparison.csv`, `comparison.json`, Lean sources and logs.

Alternatively, with Lean 4.16.0 on PATH: `python3 compare.py`.

## Important limitations

- `05_artifact_modified` simulates a trusted-artifact hash mismatch via a fixture flag, not a real secure artifact store.
- `04_statement_substitution` supplies `True` to Lean but the requested statement is `False`; B0 does not receive the external request, by design.
- Lean is NOT available in the author's execution container; no current-run Lean results can be claimed from the local dry run.
- The 12 examples are hand-designed and do not represent independent AI-generated proofs.
- `lean_ms` is one Lean execution reused by both regimes, **not** comparative end-to-end timing.
