# Writing the rules

The ratings come entirely from two files you own:

- `config/rules.yaml`: when to give a red, amber or green rating
- `config/interventions.yaml`: the library of recommended changes

Both ship with **placeholder** content written by Claude. Replace it with your own. You can edit the files on GitHub (open the file, click the pencil icon, then commit). Every change is tracked.

After any change, run the sample check (see the end of this page) to see how your rules rate the test assessments.

## How a rating is worked out

1. Each of the four checks starts at **green**: `secure`, `tier`, `valid`, `reliable`.
2. A rule **fires** when **all** of its `when` conditions are true.
3. Each check takes the **worst** rating of the rules that fired for it.
4. The **overall** rating is the worst of the four checks.

If nothing fires, everything is green. Order of rules in the file doesn't matter, except that recommendations appear in the order rules first trigger them.

## A rule

```yaml
- id: SEC-02                     # unique; shown in the report
  check: secure                  # secure | tier | valid | reliable
  when:                          # ALL of these must be true
    intended_tier: 2
    conditions: [take_home, timed_online_unsupervised]
    assessment_type: [essay, report, reflective]
  rating: amber                  # green | amber | red
  why: >                         # shown to staff; say what's wrong and why
    Written work done without supervision can be produced largely by AI...
  policy: "4.7, Table 1 (Tier 2); 5.1"   # policy section(s), shown in report
  ofs: >                         # OfS expectation (optional)
    Students can often use AI to complete unsupervised assessments...
  suggest_tier: 3                # optional: suggest a different tier
  interventions: [INT-ORAL, INT-PROCESS]   # ids from interventions.yaml
  placeholder: true              # delete this line once the rule is yours
```

`>` lets you write text over several lines; the line breaks are ignored.

## Fields you can test in `when`

| Field | Values |
|---|---|
| `assessment_type` | `essay`, `report`, `dissertation`, `reflective`, `exam`, `short_answer_quiz`, `presentation`, `portfolio`, `code`, `practical`, `oral`, `other` |
| `conditions` | `invigilated`, `supervised_in_class`, `live_oral`, `timed_online_unsupervised`, `take_home` |
| `level` | `3`, `4`, `5`, `6`, `7` |
| `weighting` | number 0–100 |
| `group` | `true` / `false` |
| `intended_tier` | `1`, `2`, `3`, `4` |
| `tier_stated_in_canvas` | `"yes"`, `"no"`, `not_sure` (**quote "yes" and "no"**) |
| `evidence_required` | a list; any of `declaration`, `interaction_log`, `prompts_outputs`, `drafts_edits`, `critical_evaluation`, `reflection` |
| `psrb` | `true` / `false` |
| `has_brief` | `true` / `false`: was a brief pasted in? |
| `has_rubric` | `true` / `false`: were marking criteria pasted in? |
| `has_evidence_requirement` | `true` / `false`: was any evidence type ticked? |

Rules can't read the free text (learning outcomes, brief, rubric). The AI reads those and raises points alongside the ratings, but it never changes a rating.

## Ways to write a condition

| You write | Meaning |
|---|---|
| `intended_tier: 1` | equals 1 |
| `intended_tier: [3, 4]` | is 3 or 4 |
| `conditions: {not: [invigilated, supervised_in_class]}` | is anything except these |
| `weighting: {min: 50}` | 50 or more |
| `weighting: {max: 20}` | 20 or less |
| `weighting: {min: 20, max: 40}` | between 20 and 40 |
| `evidence_required: {contains_any: [prompts_outputs, interaction_log]}` | at least one of these ticked |
| `evidence_required: {contains_all: [critical_evaluation, reflection]}` | all of these ticked |
| `evidence_required: {empty: true}` | none ticked |

### Watch out for "yes" and "no"

YAML reads an unquoted `yes` or `no` as true/false. Always write `"yes"` and `"no"` in quotes. The app refuses to start with a clear message if you forget.

## A recommendation

```yaml
- id: INT-ORAL
  title: Add a short oral check
  text: >
    Add a short viva or presentation in which students explain and defend
    their work.
  placeholder: true               # delete once it's yours
```

When the AI step runs, Claude rewrites `text` to fit the specific assessment, keeping its intent. If the AI step fails, staff see your `text` exactly as written.

## Checking your rules

The `samples/` folder holds test assessments, each with the ratings you'd expect. To compare:

```bash
python scripts/check_samples.py
```

It lists every sample whose ratings differ from what's expected. This uses the rules only, with no AI calls and no cost. A difference means either a rule needs changing or the expected label does. To add your own anonymised example, copy a sample file and edit it.

If a file has a mistake (unknown field, misspelt rating, unknown recommendation id), the app shows the error on screen instead of running.
