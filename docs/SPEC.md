# GenAI Assessment Check: agreed product spec

Agreed 24 November 2026 after a structured design interview. This is the record of what the prototype is and is not. Change it when a decision changes.

## Purpose

Help module leaders check **one assessment component** against:

- the University of Liverpool policy *The Use of Generative Artificial Intelligence in Learning, Teaching and Assessment* (v1.1, August 2026), and
- the Office for Students (OfS) findings on AI and assessment (November 2026, with Advance HE).

The check covers four things:

| Check | Working definition |
|---|---|
| **Secure** | How easily a student could use AI beyond the permitted tier without being detected, given the assessment's format and conditions. |
| **Tier-appropriate** | The tier matches both the learning outcomes and the conditions. Tier 1 needs supervision or controlled conditions; Tiers 3 and 4 need an evidence requirement in the brief; invigilated exams default to Tier 1 (policy 4.3, 4.7). |
| **Valid** | With the permitted AI use, the task still shows the student achieved the stated learning outcomes. |
| **Reliable** | Different markers would grade consistently given AI involvement: the criteria reward the student's own contribution, and it is clear how declared AI use affects marks. |

## Users

- **Fill it in:** module leaders, about their own assessments.
- **Test the prototype:** the project owner and a few colleagues (AQIA or friendly academics).

## Inputs (one component per run)

| # | Input | Type | Used by |
|---|---|---|---|
| 1 | Assessment type | choice | rules |
| 2 | Conditions (invigilated, supervised in class, live/oral, timed online unsupervised, take-home) | choice | rules |
| 3 | FHEQ level and weighting | choice / number | rules |
| 4 | Individual or group | choice | rules |
| 5 | Learning outcomes | free text | AI |
| 6 | Intended tier, and whether Canvas states it | choice | rules |
| 7 | For Tiers 3 and 4, the AI-use evidence the brief requires | multi-choice | rules |
| 8 | Marking criteria / rubric (optional) | free text | AI |
| 9 | Brief (optional) | free text | AI |
| 10 | PSRB or fitness-to-practise constraints | yes/no + text | rules + AI |

Leaving out the brief or rubric lowers the confidence shown in the result.

## Logic

- **Ratings:** red / amber / green for each check. The overall rating is the worst of the four. Ratings come **only from rules** (`config/rules.yaml`). The AI can flag issues but never changes a rating.
- **Tier:** staff state their intended tier; rules can suggest a different tier when it doesn't fit.
- **Recommendations:** taken from a fixed library (`config/interventions.yaml`) triggered by rules. Claude (Opus 5.5, low effort) tailors the wording to the specific assessment.
- **Citations:** each finding cites the policy section and the OfS expectation. OfS wording is **provisional** until OfS publishes how its requirements apply to AI.
- **Advisory only:** the output states that the tier decision stays with the module team (policy 10.2).
- **If the AI step fails** (error, refusal, budget limit): the rule-based ratings and standard recommendation wording are still shown, with a note that AI analysis was unavailable.

## Rules ownership

The project owner writes `config/rules.yaml` and `config/interventions.yaml` directly. `docs/RULES.md` documents the format. The first version ships with clearly marked **placeholder** rules so the app can be built and tested in parallel.

## Output

- A downloadable Word report and a JSON copy of the same result.
- A link to a Microsoft Form asking "Did this rating match your judgement? What was wrong?"

## Technology and hosting

- Python + Streamlit, hosted behind a shared password, with the Anthropic API key held server-side (Streamlit secrets).
- Budget: monthly spend limit set in the Anthropic Console, plus a cap on response length (`max_tokens`) in code.
- **Nothing is stored** on the server. Results exist only in the browser session and the downloaded files.
- Accessibility target: WCAG 2.2 AA from the start.

## Data

- Prototype uses made-up sample assessments, plus real ones **only** with the module leader's permission and with names and identifiers removed. Keep a note of who agreed.
- **Before pilot use:** get approval for the Claude API under policy sections 7 and 9, or move to the University's approved AI platform.

## Test set and success measure

About 8 made-up assessments (`samples/`), plus the owner's anonymised examples, each labelled with the expected rating. The prototype works if its ratings match those labels (`scripts/check_samples.py`).

## Out of scope for the prototype (pilot stage)

- Combining results across modules.
- Assessing a whole module at once.
- An admin page for editing rules.

## Sources

- University of Liverpool, *The Use of Generative Artificial Intelligence in Learning, Teaching and Assessment*, v1.1, August 2026.
- OfS, [Universities should help students develop AI skills while protecting confidence in degrees](https://www.officeforstudents.org.uk/news-blog-and-events/press-and-media/universities-should-help-students-develop-ai-skills-while-protecting-confidence-in-degrees/) (press release).
- OfS, [Effective institutional practice in AI](https://www.officeforstudents.org.uk/for-providers/quality-and-standards/artificial-intelligence-in-higher-education/effective-institutional-practice/).
- OfS and Advance HE, [Making AI work for students: reflections on institutional practice](https://www.officeforstudents.org.uk/publications/making-ai-work-for-students-reflections-on-institutional-practice/).
