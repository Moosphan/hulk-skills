# Intake And Defaults

## Inputs

The skill can accept:

- JD text or Markdown
- resume text or Markdown
- target level
- language preference
- optional external Markdown question bank
- optional request for local artifacts

## Default Intake Behavior

If the user does not specify details, assume:

- level: `senior`
- language: `en`
- mode: full interview
- output: in conversation first, local artifact second

## Intake Questions To Resolve Internally

Before starting the interview, Claude Code should normalize:

- what role the candidate is targeting
- whether English is required
- whether the user wants a full interview or one specific round
- whether the user wants only interview interaction or also local files
- whether an external question bank should be used

## Missing Information Policy

If some inputs are missing:

- continue with reasonable defaults when safe
- state the assumption briefly
- do not block the interview unless the missing input makes the task ambiguous in a risky way

## Intake Output

Produce a normalized working context:

```json
{
  "level": "senior",
  "language_mode": "en",
  "interview_mode": "full",
  "needs_local_artifacts": false,
  "question_bank_present": false
}
```
