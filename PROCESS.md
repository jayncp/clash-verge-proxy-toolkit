# Process

- [completed] Initialize the project with `uv`
- [completed] Create the baseline Git commit before the UDP-chain changes
- [completed] Re-apply the UDP-chain changes and create the second commit
- [completed] Run verification checks
- [completed] Store sensitive local values in ignored `docs/local/local_information.md`
- [completed] Move proxy scripts into `scripts/proxy/`
- [completed] Move local Codex.app patch helper into `scripts/local/`
- [completed] Create public `injection_component.example.yaml`
- [completed] Extract public AdsPower fingerprint example into `docs/`
- [completed] Verify public-ready layout and checks
- [completed] Rebuild Git history into clean public commits
- [completed] Re-scan Git history for sensitive values

Notes:
- `uv init` panicked twice on this macOS environment (`uv 0.9.26`), so the project metadata was created manually in the standard `uv` layout.
- `docs/local/` is local-only and ignored by Git.
