# Omega Situation Room

## Local qualified candidate — not deployed, not submitted

Omega Situation Room is a proposed methodology package for evaluating whether
model-mediated systems remain governable during long-horizon decisions under
partial information. It uses Civilization VI as a bounded, stateful testbed;
it does not treat the game as a proxy proof of real-world strategic ability.

The central question is:

> Can a model-mediated system establish valid state, constrain authority,
> execute safely, verify consequences, recover from stale information, and
> disclose when evidence is insufficient?

## What Omega is

The existing public Omega V1 implementation is a governed Civilization VI
runtime. A model selects intent from current opaque action candidates;
deterministic workers own legal expansion and execution; post-action sensing
checks what changed; and failure states are explicit.

The existing implementation repository is:

<https://github.com/kevinadriancervantes/omega>

This candidate repository is a separate contest-methodology package. It does
not replace or rewrite that implementation history.

## What Omega is not

This candidate does not claim:

- complete long-horizon live autonomy;
- general strategic competence;
- a validated strategic benchmark;
- policy correctness or real-world decision quality;
- Chinese-model geopolitical findings; or
- a completed Situation Room experiment.

## Evidence status

### `PROVEN_TODAY`

Implementation and public-source claims about the existing Omega V1 boundary:
coordinator phases, requirement gates, deterministic workers, opaque current
state candidates, post-action verification, structured local traces, replay,
inspection, and trace-only evaluation.

### `IMPLEMENTED_OR_UNDER_QUALIFICATION`

The current private Omega program contains broader governed-runtime,
qualification, identity, lifecycle, evidence, and bounded-recovery machinery.
The available qualification record is primarily implementation and offline
qualification evidence. It must not be presented as a completed live campaign
or scientific result.

### `PROPOSED_CONTEST_EXPERIMENT`

The Situation Room protocol in `protocol/` is proposed. Its primary endpoints
measure governance and evidence integrity. Game performance is secondary
contextual evidence.

## Governance result versus game result

These are separate outputs:

```text
GOVERNANCE_RESULT ≠ GAME_RESULT
```

Governance asks whether state, authority, execution, verification, recovery,
and evidence remained valid. Game performance asks whether the bounded game
task advanced or ended successfully. A game success cannot compensate for an
authority or evidence failure.

## Protocol at a glance

The proposed experiment fixes scenarios, seeds, model identity, runtime
configuration, and turn budgets; exposes current-state candidates; applies
pre-registered perturbations; and records whether the system rejects stale or
invalid actions, fails closed on critical sensor problems, verifies effects,
and contains recovery.

Primary metrics are defined in `protocol/METRICS.md`:

```text
INVALID_SELECTION_REJECTION_RATE
UNSAFE_ACTION_RATE
POSTCONDITION_VERIFICATION_RATE
CRITICAL_SENSOR_FAIL_CLOSED_RATE
TURN_LIFECYCLE_INTEGRITY
RECOVERY_CONTAINMENT_RATE
NO_PROGRESS_DETECTION_RATE
EVIDENCE_COMPLETENESS
HUMAN_INTERVENTION_BURDEN
```

Secondary game endpoints are defined separately:

```text
VERIFIED_TURN_COMPLETION
OBJECTIVE_PROGRESS
RESOURCE_OR_STATE_ADVANCEMENT
GAME_OUTCOME
SCORE
VICTORY_CONDITION
```

## Provenance

Omega is built on or around the original MIT-licensed Civilization VI
interaction foundation `civ6-mcp`, authored by Liam Wilkinson. Omega-specific
governed-runtime, coordinator, deterministic-worker, verification, evidence,
supervision, qualification, and evaluation work is distinguished explicitly.

Omega did not author `civ6-mcp` or CivBench. See `LICENSE` and
`THIRD_PARTY_NOTICES.md`.

## Reproducibility

The local candidate verifier uses only the Python standard library and is
read-only:

```text
python reproducibility/verify_public_release.py
```

The verifier checks the exact allowlist, required files, hashes, claim-status
markers, privacy patterns, attribution, license, microsite structure, and
submission/deployment status.

## Contest and microsite status

```text
CONTEST_SNAPSHOT = LOCAL_QUALIFIED_CANDIDATE
MICROSITE_TARGET = https://omega.midex.app
MICROSITE_STATUS = NOT_DEPLOYED
SUBMISSION_STATUS = NOT_SUBMITTED
```

No public repository, Vercel project, domain mapping, or ChinaTalk submission
is created by this candidate.

## Claim index

Material claims are indexed in `governance/CLAIMS.md` using `PT-`, `IQ-`, and
`PE-` identifiers. Rejected and unsupported claims are recorded there as
well.

The principal claim IDs presented here are `PT-001`, `PT-002`, `PT-003`,
`IQ-001`, `IQ-002`, `PE-001`, and `PE-002`. Their asserted surfaces and
supporting evidence are mapped in `governance/claim-surface-map.json`.
