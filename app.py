"""GenAI Assessment Check: Streamlit app.

Run locally:  streamlit run app.py
Settings come from .streamlit/secrets.toml (see secrets.toml.example).
"""

from __future__ import annotations

import hmac
import os
import re

import anthropic
import streamlit as st

from gac import ADVISORY_NOTE, APP_NAME, OFS_NOTE
from gac.check import run_check
from gac.models import (
    ASSESSMENT_TYPES,
    CANVAS_STATED,
    CHECKS,
    CONDITIONS,
    EVIDENCE_TYPES,
    LEVELS,
    RATING_LABELS,
    TIERS,
    AssessmentInput,
)
from gac.report import to_docx, to_json
from gac.rules import RulesError, load

st.set_page_config(page_title=APP_NAME, layout="centered")

SYMBOL = {"green": "🟢", "amber": "🟠", "red": "🔴"}


def secret(name: str, default: str = "") -> str:
    try:
        value = st.secrets.get(name)
    except FileNotFoundError:
        value = None
    return value or os.environ.get(name, default)


# ---- Password gate ------------------------------------------------------


def password_ok() -> bool:
    expected = secret("APP_PASSWORD")
    if not expected:
        return True  # no password configured (local development)
    if st.session_state.get("authenticated"):
        return True
    st.title(APP_NAME)
    with st.form("login"):
        pw = st.text_input("Password", type="password")
        if st.form_submit_button("Sign in"):
            if hmac.compare_digest(pw.encode(), expected.encode()):
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("That password is not correct.")
    return False


if not password_ok():
    st.stop()


# ---- Setup --------------------------------------------------------------


@st.cache_resource
def get_rules():
    return load()


try:
    ruleset = get_rules()
except RulesError as e:
    st.error(f"The rules files have a problem, so the check cannot run.\n\n{e}")
    st.stop()

api_key = secret("ANTHROPIC_API_KEY")
client = anthropic.Anthropic(api_key=api_key, timeout=120, max_retries=1) if api_key else None
feedback_url = secret("FEEDBACK_FORM_URL")


# ---- Form ---------------------------------------------------------------

st.title(APP_NAME)
st.write(
    "Check one assessment component against the University's policy on generative AI "
    "in assessment. You'll get a rating for whether it is secure, tier-appropriate, "
    "valid and reliable, with suggested changes."
)
st.info(ADVISORY_NOTE)
if ruleset and any(r.get("placeholder") for r in ruleset.rules):
    st.warning(
        "Prototype: the rules are placeholders and have not been approved. "
        "Use made-up or permitted example assessments only."
    )

with st.form("assessment"):
    st.header("About the assessment")
    title = st.text_input("Assessment name (optional)", help="For your own reference, e.g. 'ENGL201 Essay 2'.")
    assessment_type = st.selectbox(
        "Assessment type", list(ASSESSMENT_TYPES), format_func=ASSESSMENT_TYPES.get
    )
    conditions = st.selectbox(
        "Conditions", list(CONDITIONS), format_func=CONDITIONS.get,
        help="Where and how students complete the assessment.",
    )
    level = st.selectbox("FHEQ level", list(LEVELS), index=1, format_func=LEVELS.get)
    weighting = st.number_input("Weighting (% of module mark)", min_value=0, max_value=100, value=50, step=5)
    group = st.radio("Individual or group?", ["Individual", "Group"], horizontal=True) == "Group"
    learning_outcomes = st.text_area(
        "Learning outcomes assessed (required)", height=150,
        help="Paste the learning outcomes this component assesses.",
    )

    st.header("GenAI tier")
    intended_tier = st.selectbox("Intended tier", list(TIERS), index=1, format_func=TIERS.get)
    tier_stated_in_canvas = st.radio(
        "Is the tier stated on the assessment's Canvas page?",
        list(CANVAS_STATED), format_func=CANVAS_STATED.get, horizontal=True,
    )
    evidence_required = st.multiselect(
        "Tier 3 and 4 only: what evidence of AI use does the brief require?",
        list(EVIDENCE_TYPES), format_func=EVIDENCE_TYPES.get,
        help="Leave empty for Tier 1 or 2, or if the brief doesn't ask for any.",
    )

    st.header("Professional requirements")
    psrb = st.radio(
        "Does a PSRB or fitness-to-practise requirement apply?", ["No", "Yes"], horizontal=True
    ) == "Yes"
    psrb_details = st.text_area("If yes, briefly describe it (optional)", height=80)

    st.header("Brief and marking criteria")
    st.write(
        "Optional, but the check is more confident with them. Remove names and anything "
        "that identifies a person before pasting."
    )
    brief = st.text_area("Assessment brief (optional)", height=200)
    rubric = st.text_area("Marking criteria or rubric (optional)", height=200)

    submitted = st.form_submit_button("Check this assessment", type="primary")


# ---- Run ----------------------------------------------------------------

if submitted:
    a = AssessmentInput(
        title=title.strip(),
        assessment_type=assessment_type,
        conditions=conditions,
        level=level,
        weighting=int(weighting),
        group=group,
        learning_outcomes=learning_outcomes,
        intended_tier=intended_tier,
        tier_stated_in_canvas=tier_stated_in_canvas,
        evidence_required=evidence_required,
        psrb=psrb,
        psrb_details=psrb_details,
        brief=brief,
        rubric=rubric,
    )
    problems = a.validate()
    if problems:
        st.error("Please fix the following:\n\n" + "\n".join(f"- {p}" for p in problems))
        st.session_state.pop("result", None)
    else:
        with st.spinner("Checking the assessment. This can take up to a minute."):
            st.session_state.result = run_check(a, ruleset, client)


# ---- Results ------------------------------------------------------------

result = st.session_state.get("result")
if result:
    st.divider()
    st.header("Results")
    st.subheader(f"Overall: {SYMBOL[result.overall]} {RATING_LABELS[result.overall]}")
    for check, label in CHECKS.items():
        r = result.ratings[check]
        st.markdown(f"- **{label}:** {SYMBOL[r]} {RATING_LABELS[r]}")
    st.caption(f"Confidence: {result.confidence.capitalize()}. {result.confidence_reason}")

    if result.suggested_tiers:
        st.warning(
            "Consider a different tier: "
            + "; ".join(TIERS[t] for t in result.suggested_tiers)
        )

    st.subheader("Findings")
    if not result.findings:
        st.write("The current rules found no concerns.")
    for f in result.findings:
        with st.container(border=True):
            st.markdown(f"**{CHECKS[f.check]}: {SYMBOL[f.rating]} {RATING_LABELS[f.rating]}**")
            st.write(f.why)
            refs = []
            if f.policy:
                refs.append(f"University policy section {f.policy}")
            if f.ofs:
                refs.append(f"OfS: {f.ofs}")
            if refs:
                st.caption(" · ".join(refs))

    st.subheader("Points raised by AI review")
    if result.ai_ran:
        if result.ai_flags:
            for flag in result.ai_flags:
                quote = f' (from: "{flag.evidence}")' if flag.evidence else ""
                st.markdown(f"- **{CHECKS[flag.check]}:** {flag.concern}{quote}")
        else:
            st.write("No further points.")
        st.caption("These points do not change the ratings.")
    else:
        st.info(result.ai_note + " The ratings and standard recommendations below are unaffected.")

    st.subheader("Recommendations")
    if not result.recommendations:
        st.write("No changes recommended by the current rules.")
    for r in result.recommendations:
        st.markdown(f"**{r.title}**")
        st.write(r.text)

    st.subheader("Download")
    slug = re.sub(r"[^A-Za-z0-9]+", "-", result.input.title).strip("-") or "assessment"
    col1, col2 = st.columns(2)
    col1.download_button(
        "Download report (Word)", to_docx(result), file_name=f"genai-check-{slug}.docx",
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )
    col2.download_button(
        "Download record (JSON)", to_json(result), file_name=f"genai-check-{slug}.json",
        mime="application/json",
    )
    st.caption("Nothing is saved by this app. Download the report if you want to keep it.")

    if feedback_url:
        st.subheader("Feedback")
        st.markdown(
            f"Did this rating match your judgement? [Tell us in a short form]({feedback_url})."
        )

st.divider()
st.caption(OFS_NOTE)
