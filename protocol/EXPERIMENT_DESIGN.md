# Proposed Situation Room experiment V1

Status: `PROPOSED_CONTEST_EXPERIMENT` (`PE-001`, `PE-002`)

> THIS EXPERIMENT HAS NOT YET PRODUCED A VALIDATED PUBLIC STRATEGIC RESULT.

## Design objective

Measure whether a model-mediated strategic runtime remains governable when
state becomes stale, sensors fail, requirements change, and local actions do
not produce progress.

## Fixed conditions

Future execution should pre-register:

- scenario definitions and map/game seeds;
- civilization, leader, difficulty, speed, and game version;
- model identity, prompt/playbook, endpoint, and parameters;
- tool/runtime version and source identity;
- turn horizon and wall-clock budget;
- intervention and recovery budgets;
- evidence schema and retention policy.

## Proposed conditions

At minimum, the matrix should contain:

1. a nominal governed condition;
2. stale-candidate perturbations;
3. critical-sensor unavailable or stale conditions;
4. repeated-no-progress conditions;
5. declared requirement-change conditions;
6. a held-out scenario family not used while tuning the protocol.

The perturbation schedule must be known to the adjudication design but hidden
from the model where the condition requires an unanticipated failure.

## Horizon

Use a short pilot horizon to validate measurement and a separately declared
longer horizon for the contest experiment. Exact turn counts and sample size
must be chosen after feasibility and power analysis; this candidate invents no
sample-size claim.

## Primary endpoints

The primary endpoints are the governance metrics in `METRICS.md`:

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

## Secondary endpoints

Report verified turn completion, objective progress, resource/state
advancement, game outcome, score, and victory condition separately.

## Invalid-run rules

Exclude a run from ordinary pooled performance analysis if identity, authority,
event ordering, evidence custody, or declared controls fail. Retain its
failure classification in the audit summary. Never delete or silently repair
the raw event history.

## Evidence custody

Retain private raw evidence under the laboratory's existing controls. Publish
only derived status matrices, aggregate metrics, selected safe fixtures, and
hash/source references. Every public evidence item must state its origin,
derivation method, supported claim, privacy classification, and qualification
level.

## Interpretation

The experiment can speak to governability and bounded runtime behavior in the
declared testbed. It cannot establish policy correctness, real-world strategic
competence, hidden beliefs, intent, deception, or general autonomy.
