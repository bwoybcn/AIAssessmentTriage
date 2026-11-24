# GenAI Assessment Check

*(Repository name: AIAssessmentTriage. Working title: OfS Assessment Wizard.)*

A prototype web app that helps module leaders check one assessment component against the University of Liverpool's policy on generative AI in assessment (v1.1, August 2026) and the Office for Students' November 2026 findings on AI and assessment.

It rates whether the assessment is **secure**, **tier-appropriate**, **valid** and **reliable** (red / amber / green), suggests changes, and produces a downloadable Word report and JSON record. Ratings come from editable rules; Claude reads the brief and rubric to raise further points and tailor the recommendations, but never changes a rating.

**Status: prototype.** The rules are placeholders. Use only made-up example assessments, or real ones with the module leader's permission and identifiers removed. See [docs/DESIGN.md](docs/DESIGN.md).

## Files

| Path | What it is |
|---|---|
| `app.py` | The Streamlit web app |
| `config/rules.yaml` | When to rate red / amber / green (**you edit this**) |
| `config/interventions.yaml` | Library of recommended changes (**you edit this**) |
| `docs/RULES.md` | How to write rules |
| `docs/DESIGN.md` | The agreed design |
| `samples/` | Test assessments with expected ratings |
| `scripts/check_samples.py` | Compares rule ratings with expected ratings |
| `gac/` | The engine: rules, Claude step, reports |
| `tests/` | Automated tests |

## Run it on your computer

Needs Python 3.10 or later.

```bash
pip install -r requirements.txt
```

```bash
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
```

Edit `.streamlit/secrets.toml` and add your Anthropic API key. Without a key the app still works, using rules only.

```bash
streamlit run app.py
```

## Put it online for colleagues (Streamlit Community Cloud)

1. Sign in at [share.streamlit.io](https://share.streamlit.io) with GitHub and create an app from this repository, main file `app.py`.
2. In the app's **Settings → Secrets**, paste the contents of `secrets.toml.example` with real values: `ANTHROPIC_API_KEY`, a shared `APP_PASSWORD`, and your Microsoft Form link as `FEEDBACK_FORM_URL`.
3. Share the link and password with testers.

Streamlit Community Cloud runs outside the UK. That's fine for made-up samples, but factor it into the approval needed before pilot use.

## Cost controls

- Set a **monthly spend limit** in the Anthropic Console (Settings → Limits). When it's reached, the app keeps working with rules only.
- Each run is capped at 6,000 output tokens (`MAX_TOKENS` in `gac/ai.py`) and uses Claude Opus 5.5 at low effort.
- If Opus declines a request on safety grounds, the API automatically retries on a fallback model in the same call (server-side fallback, enabled in `gac/ai.py`).

## Tests

```bash
python -m pytest
```

```bash
python scripts/check_samples.py
```

## Accessibility

The app is built to WCAG 2.2 AA: every input has a visible label, ratings are always written out in words (not shown by colour alone), and the Word report uses real headings and tables. Streamlit itself is not certified as fully WCAG compliant, so test with a screen reader and keyboard before the pilot.
