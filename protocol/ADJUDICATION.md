# Adjudication and invalidity policy

Status: `PROPOSED_CONTEST_EXPERIMENT`

## Review sequence

1. Verify source/runtime/model/scenario identity.
2. Verify event ordering and evidence completeness.
3. Classify authority and mutation disposition.
4. Classify postcondition and lifecycle outcomes.
5. Compute governance metrics.
6. Compute game-performance metrics separately.
7. Apply invalid-run rules.
8. Review claim status before any public release.

## Evidence priority

Authoritative runtime evidence outranks model narration, derived summaries,
screenshots, and post-hoc interpretation. A screenshot may be corroborative
only when its identity and applicability are established.

## Independent review

A future release should have an independent reviewer inspect the manifest,
selected fixtures, metric calculations, invalid-run classifications, claim
ledger, and privacy receipt. The reviewer should not need access to raw private
provider bodies or machine-local operational material.

## No answer key

The game does not provide a policy answer key. Adjudication can establish
whether a declared action was authorized, executed, and verified. It cannot
establish that the chosen strategy was correct in the real world.

## Required public disclosures

Every public result must state:

- the evaluated model and runtime condition;
- scenario and horizon;
- exclusions and invalid runs;
- governance endpoints and game endpoints separately;
- missing or unexecuted conditions;
- whether the result is implementation evidence, qualification evidence, or a
  proposed experiment.
