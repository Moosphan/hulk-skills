# Follow-Up Policy

## Core Rule

Every follow-up must be grounded in the candidate's latest answer.

Do not ask generic follow-ups if a specific claim, omission, or contradiction can be probed instead.

## Follow-Up Types

- evidence probe
  - when the answer has claims but no concrete example
- ownership probe
  - when the answer says `we` but personal responsibility is unclear
- metrics probe
  - when the answer claims improvement without baseline, metric, or result
- tradeoff probe
  - when the answer says what was done but not why
- failure probe
  - when the answer presents only success and hides risk or rollback
- contradiction probe
  - when the answer conflicts with earlier claims
- depth probe
  - when the answer sounds conceptually correct but implementation depth is unclear
- scale probe
  - when the candidate claims complex scope, high traffic, or cross-team influence

## Follow-Up Escalation

Escalate in this order when possible:

1. clarify
2. request concrete evidence
3. deepen implementation detail
4. probe tradeoffs or metrics
5. challenge contradiction
6. mark risk

## Stop Conditions

Stop following up on a topic when:

- ownership is clear
- metric/baseline/outcome is clear enough
- tradeoff and rejected alternative are explicit
- the candidate's actual depth boundary is exposed
- the contradiction is either resolved or confirmed as a risk

## Interaction Rule

- ask one question at a time
- keep the chain short and purposeful
- do not stack multiple asks into one long prompt unless necessary
