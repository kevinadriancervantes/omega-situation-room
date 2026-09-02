# Public-candidate verifier

Run from the candidate root:

```text
python reproducibility/verify_public_release.py
```

The verifier is read-only. It checks exact allowlist membership, required
files, payload hashes, manifest and seal identities, privacy markers,
attribution, license scope, CFF 1.2.0 semantics, claim-surface reconciliation,
microsite structure, and the invariants `NOT_SUBMITTED` and `NOT_DEPLOYED`.

When run inside the local Git candidate, it also checks author and committer
metadata without printing addresses. Non-public local history is accepted
only when the manifest requires a fresh one-commit public projection.

It does not contact a network, run a model, start a game, start FireTuner,
deploy a site, change a repository, or submit a form.
