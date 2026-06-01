# Interview Flow

## High-Level State Machine

Use this sequence:

- `intake`
- `screening`
- `planning`
- `round_active`
- `round_review`
- `reporting`
- `completed`

## Default Rounds

- `intro`
  - self-introduction and strongest project anchor
- `screening`
  - resume authenticity, ownership, baseline fit
- `round1`
  - Android core, implementation detail, problem solving
- `round2`
  - architecture, performance, tradeoffs, diagnosis depth
- `round3`
  - technical influence, business judgment, cross-team execution
- `hr`
  - motivation, stability, conflict handling, maturity

## Question Loop

For each question:

1. Ask one main question.
2. Read the answer carefully.
3. Score the answer with evidence and confidence.
4. Decide whether to:
   - follow up on the same topic
   - switch topic
   - increase difficulty
   - decrease difficulty
   - mark a risk
   - complete the round
   - terminate the round

## Round Review

At the end of each round:

- summarize strengths
- summarize risks
- summarize missing evidence
- decide `advance`, `advance_with_risk`, `borderline`, or `reject`
- optionally carry unresolved risk into the next round

## Early Termination

Terminate early only when:

- project ownership appears fabricated
- contradictions remain unresolved after direct challenge
- architecture depth is clearly below required level for the target role
- the candidate cannot participate in the required language mode at all

## Output Requirement

Every round should leave behind enough structure to explain:

- what was asked
- why it was asked
- what evidence was collected
- why the result was pass, risk, borderline, or reject
