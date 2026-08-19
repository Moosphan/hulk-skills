# Intake And Defaults

## Inputs

The skill can accept:

- target role or template intent
- request to create a new reusable user template through conversation
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

- which preset or user template should be used
- whether the user wants to create a new local reusable template first
- what role the candidate is targeting
- whether English is required
- whether the user wants a full interview or one specific round
- whether the user wants only interview interaction or also local files
- whether an external question bank should be used
- whether JD and resume were provided as a local path, URL, or inline text

## Missing Information Policy

If some inputs are missing:

- continue with reasonable defaults when safe
- state the assumption briefly
- do not block the interview unless the missing input makes the task ambiguous in a risky way

Material handling policy:

- if JD and resume are both present, continue normally
- if only one of them is present, explain that interview precision will drop and ask whether to continue
- if neither is present, collect them first unless the user explicitly requests a generic mock interview

Conversational setup policy:

- if the user says things like “帮我新建一个岗位模板” or “create a new role template”, switch into template-creation Q&A before the interview
- collect at least: `display_name`, `target_role`, `role_family`, `candidate_level`, `default_language`, optional `inherits_from`, and optional aliases
- save the generated template locally under `data/user-templates/`
- after the template is created, continue with JD / resume collection and use the new user template first

## Intake Output

Produce a normalized working context:

```json
{
  "template_resolution": {
    "template_id": "android_senior",
    "source": "preset"
  },
  "level": "senior",
  "language_mode": "en",
  "interview_mode": "full",
  "needs_local_artifacts": false,
  "question_bank_present": false,
  "materials": {
    "jd": {
      "type": "file_path",
      "value": "/path/to/jd.md",
      "resolved": true
    },
    "resume": {
      "type": "url",
      "value": "https://example.com/resume.md",
      "resolved": true
    }
  },
  "missing_materials": []
}
```
