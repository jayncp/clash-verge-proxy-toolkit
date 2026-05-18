# Public Release Sanitization Plan

## Goals

- Keep local sensitive values usable in ignored local files.
- Publish only example configuration with sensitive fields blanked.
- Move user-facing docs under `docs/`.
- Group executable scripts under `scripts/`.
- Rewrite Git history so sensitive values are absent from all public commits.

## Steps

- [x] Store sensitive local values in `docs/local/local_information.md`.
- [x] Ignore `docs/local/`, generated exports, system profile dumps, and local proxy config.
- [x] Move proxy scripts to `scripts/proxy/`.
- [x] Move local app patch helper to `scripts/local/`.
- [x] Create `injection_component.example.yaml`.
- [x] Extract AdsPower fingerprint into a public example document.
- [x] Rewrite README for the cleaned layout.
- [x] Run typecheck, lint, and script smoke checks.
- [x] Rebuild Git history into clean public commits.
- [x] Re-scan the final history for sensitive values.
