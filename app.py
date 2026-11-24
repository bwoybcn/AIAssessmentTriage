"""GenAI Assessment Check: Streamlit app.

Run locally:  streamlit run app.py
Settings come from .streamlit/secrets.toml (see secrets.toml.example).
"""

from __future__ import annotations

import hmac
import os
import re
from html import escape

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
from gac.style import CSS, logo

st.set_page_config(page_title=APP_NAME, page_icon="assets/icon.png", layout="centered")
st.html(CSS)

STEPS = ["Assessment", "Outcomes", "GenAI tier", "Brief", "Review"]
RESULTS = len(STEPS)

DEFAULTS = {
    "title": "",
    "assessment_type": "essay",
    "conditions": "take_home",
    "level": 4,
    "weighting": 50,
    "group": False,
    "learning_outcomes": "",
    "psrb": False,
    "psrb_details": "",
    "intended_tier": 2,
    "tier_stated_in_canvas": "yes",
    "evidence_required": [],
    "brief": "",
    "rubric": "",
}
STEP_FIELDS = [
    ["title", "assessment_type", "conditions", "level", "weighting", "group"],
    ["learning_outcomes", "psrb", "psrb_details"],
    ["intended_tier", "tier_stated_in_canvas", "evidence_required"],
    ["brief", "rubric"],
    [],
]

ICON = {"red": "✕", "amber": "!", "green": "✓"}
HEADLINE = {
    "red": ("Changes needed", "At least one check raised a serious concern. Start with the recommendations below."),
    "amber": ("Worth reviewing", "Nothing serious, but some points deserve a look before the assessment runs."),
    "green": ("No concerns found", "The current rules found nothing to change. Check the AI review points too."),
}
CHECK_HINT = {
    "secure": "Could students use AI beyond the tier without it being detected?",
    "tier": "Does the tier fit the learning outcomes and conditions?",
    "valid": "Does the task still show the learning outcomes were met?",
    "reliable": "Would different markers grade consistently?",
}


# ---- Helpers ------------------------------------------------------------


def secret(name: str, default: str = "") -> str:
    try:
        value = st.secrets.get(name)
    except FileNotFoundError:
        value = None
    return value or os.environ.get(name, default)


def pill(rating: str, large: bool = False) -> str:
    size = " lg" if large else ""
    return (
        f'<span class="gac-pill {rating}{size}"><span aria-hidden="true">{ICON[rating]}</span>'
        f"{RATING_LABELS[rating]}</span>"
    )


def brand_bar() -> None:
    st.html(
        f'<div class="gac-brand">{logo(28)}<span class="gac-brand-name">{APP_NAME}</span>'
        '<span class="gac-badge">Prototype</span></div>'
    )


def footer() -> None:
    st.html(
        f'<div class="gac-footer">{escape(ADVISORY_NOTE)}<br>{escape(OFS_NOTE)}<br>'
        "Nothing you enter is stored by this app.</div>"
    )


def field_key(name: str) -> str:
    return f"w_{name}"


def prime(fields: list[str]) -> None:
    """Load saved answers into widget state before the widgets are drawn."""
    for f in fields:
        if field_key(f) not in st.session_state:
            st.session_state[field_key(f)] = st.session_state.data[f]


def save(fields: list[str]) -> None:
    for f in fields:
        if field_key(f) in st.session_state:
            st.session_state.data[f] = st.session_state[field_key(f)]
    data = st.session_state.data
    if data["intended_tier"] < 3:
        data["evidence_required"] = []
    if not data["psrb"]:
        data["psrb_details"] = ""


def go(step: int) -> None:
    save(STEP_FIELDS[st.session_state.step] if st.session_state.step < RESULTS else [])
    st.session_state.error = ""
    st.session_state.step = step


def next_step() -> None:
    step = st.session_state.step
    save(STEP_FIELDS[step])
    if step == 1 and not st.session_state.data["learning_outcomes"].strip():
        st.session_state.error = "Add the learning outcomes this component assesses to continue."
        return
    st.session_state.error = ""
    st.session_state.step = step + 1


def reset() -> None:
    for k in list(st.session_state):
        if k.startswith("w_") or k in ("data", "result", "step", "error"):
            del st.session_state[k]


# ---- Password gate ------------------------------------------------------


def password_ok() -> bool:
    expected = secret("APP_PASSWORD")
    if not expected or st.session_state.get("authenticated"):
        return True
    st.html(
        f'<div class="gac-signin">{logo(56)}<h1>{APP_NAME}</h1>'
        "<p>Check whether an assessment is secure, tier-appropriate, valid and reliable "
        "under the University's policy on generative AI.</p></div>"
    )
    _, mid, _ = st.columns([1, 2, 1])
    with mid, st.form("login", border=False):
        pw = st.text_input("Access password", type="password")
        if st.form_submit_button("Sign in", type="primary", use_container_width=True):
            if hmac.compare_digest(pw.encode(), expected.encode()):
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("That password isn't right. Check with the person who shared this link.")
    footer()
    return False


if not password_ok():
    st.stop()


# ---- Setup --------------------------------------------------------------


@st.cache_resource
def get_rules():
    return load()


brand_bar()
try:
    ruleset = get_rules()
except RulesError as e:
    st.error(f"The rules files have a problem, so the check can't run.\n\n{e}")
    st.stop()

api_key = secret("ANTHROPIC_API_KEY")
client = anthropic.Anthropic(api_key=api_key, timeout=120, max_retries=1) if api_key else None
feedback_url = secret("FEEDBACK_FORM_URL")
placeholder_rules = any(r.get("placeholder") for r in ruleset.rules)

st.session_state.setdefault("data", dict(DEFAULTS))
st.session_state.setdefault("step", 0)
st.session_state.setdefault("error", "")
step = st.session_state.step
data = st.session_state.data


# ---- Wizard -------------------------------------------------------------


def stepper(current: int) -> None:
    items = []
    for i, name in enumerate(STEPS):
        state = "done" if i < current else "current" if i == current else "todo"
        aria = ' aria-current="step"' if i == current else ""
        items.append(f'<li class="{state}"{aria}><span class="bar"></span><span class="name">{name}</span></li>')
    st.html(f'<ol class="gac-steps" aria-label="Progress">{"".join(items)}</ol>')
    st.html(f'<div class="gac-step-count">Step {current + 1} of {len(STEPS)}</div>')


def nav(back: bool = True, next_label: str = "Continue") -> None:
    if st.session_state.error:
        st.error(st.session_state.error)
    st.write("")
    left, _, right = st.columns([1, 1, 1])
    if back:
        left.button("Back", on_click=go, args=(st.session_state.step - 1,), use_container_width=True)
    right.button(next_label, type="primary", on_click=next_step, use_container_width=True)


if step < RESULTS:
    if step == 0:
        st.html('<div class="gac-eyebrow">Assessment check</div>')
        st.title("Is your assessment ready for generative AI?")
        st.write(
            "Answer a few questions about one assessment component. You'll get a clear rating "
            "for whether it is secure, tier-appropriate, valid and reliable, with practical "
            "changes to consider. It takes about five minutes."
        )
        if placeholder_rules:
            st.warning(
                "Prototype: the rules haven't been approved yet. Use made-up examples, "
                "or real ones only with the author's permission and names removed."
            )
    stepper(step)
    prime(STEP_FIELDS[step])

    if step == 0:
        st.header("About the assessment")
        st.text_input("Assessment name (optional)", key="w_title",
                      placeholder="e.g. HIST204 Essay 2", help="For your own reference. It appears on the report.")
        st.selectbox("Assessment type", list(ASSESSMENT_TYPES), format_func=ASSESSMENT_TYPES.get, key="w_assessment_type")
        st.selectbox("Conditions", list(CONDITIONS), format_func=CONDITIONS.get, key="w_conditions",
                     help="Where and how students complete it.")
        c1, c2 = st.columns(2)
        c1.selectbox("FHEQ level", list(LEVELS), format_func=LEVELS.get, key="w_level")
        c2.number_input("Weighting (% of module)", min_value=0, max_value=100, step=5, key="w_weighting")
        st.radio("Individual or group work?", [False, True], key="w_group", horizontal=True,
                 format_func=lambda g: "Group" if g else "Individual")
        nav(back=False)

    elif step == 1:
        st.header("Learning outcomes")
        st.text_area("Learning outcomes this component assesses", key="w_learning_outcomes", height=180,
                     placeholder="LO1 Evaluate…\nLO2 Construct…")
        st.radio("Does a PSRB or fitness-to-practise requirement apply?", [False, True], key="w_psrb",
                 horizontal=True, format_func=lambda v: "Yes" if v else "No")
        if st.session_state.w_psrb:
            st.text_area("Briefly describe the requirement (optional)", key="w_psrb_details", height=90,
                         placeholder="e.g. NMC proficiency standards")
        nav()

    elif step == 2:
        st.header("GenAI tier")
        st.selectbox("Which tier do you intend to set?", list(TIERS), format_func=TIERS.get, key="w_intended_tier")
        st.radio("Is the tier stated on the assessment's Canvas page?", list(CANVAS_STATED),
                 format_func=CANVAS_STATED.get, key="w_tier_stated_in_canvas", horizontal=True)
        if st.session_state.w_intended_tier >= 3:
            st.multiselect("What evidence of AI use does the brief require?", list(EVIDENCE_TYPES),
                           format_func=EVIDENCE_TYPES.get, key="w_evidence_required",
                           placeholder="Choose all that apply",
                           help="Tiers 3 and 4 must say what evidence students submit (policy 4.7).")
        nav()

    elif step == 3:
        st.header("Brief and marking criteria")
        st.write(
            "Both are optional, but the check is more confident with them. "
            "Remove names and anything that identifies a person before pasting."
        )
        st.text_area("Assessment brief", key="w_brief", height=220)
        st.text_area("Marking criteria or rubric", key="w_rubric", height=220)
        nav()

    elif step == 4:
        st.header("Check your answers")

        def rows(pairs):
            return "".join(f"<tr><th scope='row'>{escape(k)}</th><td>{escape(v)}</td></tr>" for k, v in pairs)

        def preview(text: str, limit: int = 160) -> str:
            text = " ".join(text.split())
            return "Not provided" if not text else text if len(text) <= limit else text[:limit] + "…"

        sections = [
            ("Assessment", 0, [
                ("Name", data["title"] or "Not given"),
                ("Type", ASSESSMENT_TYPES[data["assessment_type"]]),
                ("Conditions", CONDITIONS[data["conditions"]]),
                ("Level and weighting", f"{LEVELS[data['level']]}, {data['weighting']}%"),
                ("Individual or group", "Group" if data["group"] else "Individual"),
            ]),
            ("Outcomes", 1, [
                ("Learning outcomes", preview(data["learning_outcomes"])),
                ("PSRB or fitness to practise", "Yes" if data["psrb"] else "No"),
            ]),
            ("GenAI tier", 2, [
                ("Intended tier", TIERS[data["intended_tier"]]),
                ("Stated in Canvas", CANVAS_STATED[data["tier_stated_in_canvas"]]),
                *([("Evidence required", ", ".join(EVIDENCE_TYPES[e] for e in data["evidence_required"]) or "None")]
                  if data["intended_tier"] >= 3 else []),
            ]),
            ("Brief", 3, [
                ("Brief", preview(data["brief"])),
                ("Marking criteria", preview(data["rubric"])),
            ]),
        ]
        for name, target, pairs in sections:
            head, edit = st.columns([4, 1], vertical_alignment="bottom")
            head.subheader(name)
            edit.button("Edit", key=f"edit_{target}", on_click=go, args=(target,), use_container_width=True,
                        help=f"Change your {name.lower()} answers")
            st.html(f'<table class="gac-review">{rows(pairs)}</table>')

        st.write("")
        left, _, right = st.columns([1, 1, 1])
        left.button("Back", on_click=go, args=(3,), use_container_width=True)
        if right.button("Run the check", type="primary", use_container_width=True):
            a = AssessmentInput(**{**data, "title": data["title"].strip(), "weighting": int(data["weighting"])})
            with st.status("Checking your assessment…", expanded=True) as status:
                st.write("Applying the policy rules")
                if client:
                    st.write("Reviewing the brief and rubric with AI (up to a minute)")
                result = run_check(a, ruleset, client)
                status.update(label="Check complete", state="complete")
            st.session_state.result = result
            st.session_state.step = RESULTS
            st.rerun()

    footer()
    st.stop()


# ---- Results ------------------------------------------------------------

result = st.session_state.get("result")
if result is None:
    reset()
    st.rerun()

a = result.input
head, sub = HEADLINE[result.overall]
st.html('<div class="gac-eyebrow">Results</div>')
st.title(a.title or "Your assessment")

suggest = ""
if result.suggested_tiers:
    names = "; ".join(TIERS[t] for t in result.suggested_tiers)
    suggest = f"<br>Tier to consider instead of Tier {a.intended_tier}: <strong>{escape(names)}</strong>"
st.html(
    f'<section class="gac-overall" aria-label="Overall rating">{pill(result.overall, large=True)}'
    f"<h2>{head}</h2><p>{sub}</p>"
    f'<div class="gac-meta">Confidence: <strong>{result.confidence.capitalize()}</strong>. '
    f"{escape(result.confidence_reason)}{suggest}</div></section>"
)

cards = []
for check, label in CHECKS.items():
    rating = result.ratings[check]
    n = sum(1 for f in result.findings if f.check == check)
    count = "No concerns found" if n == 0 else f"{n} finding{'s' if n > 1 else ''}"
    cards.append(
        f'<div class="gac-card {rating}"><div class="label">{label}</div>{pill(rating)}'
        f'<div class="desc">{CHECK_HINT[check]}<br><strong>{count}</strong></div></div>'
    )
st.html(f'<div class="gac-grid" role="list" aria-label="Ratings by check">'
        + "".join(f'<div role="listitem">{c}</div>' for c in cards) + "</div>")

if placeholder_rules:
    st.warning("Prototype: these ratings come from placeholder rules that haven't been approved.")
if not result.ai_ran:
    st.info(f"{result.ai_note} The ratings and standard recommendations are unaffected.")

tab_rec, tab_find, tab_ai, tab_you = st.tabs(
    [f"Recommendations ({len(result.recommendations)})", f"Findings ({len(result.findings)})",
     f"AI review ({len(result.ai_flags)})", "Your answers"]
)

with tab_rec:
    if not result.recommendations:
        st.write("No changes recommended by the current rules.")
    items = []
    for r in result.recommendations:
        tag = '<span class="gac-tag">Tailored</span>' if r.tailored else ""
        items.append(f'<div class="gac-item"><h4>{escape(r.title)}{tag}</h4><p>{escape(r.text)}</p></div>')
    if items:
        st.html("".join(items))

with tab_find:
    if not result.findings:
        st.write("The current rules found no concerns.")
    items = []
    for f in result.findings:
        refs = []
        if f.policy:
            refs.append(f"University policy: section {escape(f.policy)}")
        if f.ofs:
            refs.append(f"OfS (provisional): {escape(f.ofs)}")
        ref_html = f'<div class="gac-ref">{"<br>".join(refs)}</div>' if refs else ""
        items.append(
            f'<div class="gac-item">{pill(f.rating)}<h4>{CHECKS[f.check]}</h4>'
            f"<p>{escape(f.why)}</p>{ref_html}</div>"
        )
    if items:
        st.html("".join(items))

with tab_ai:
    if not result.ai_ran:
        st.write(result.ai_note)
    elif not result.ai_flags:
        st.write("The AI review found nothing further to raise.")
    else:
        items = []
        for flag in result.ai_flags:
            quote = f'<div class="gac-ref">From: “{escape(flag.evidence)}”</div>' if flag.evidence else ""
            items.append(f'<div class="gac-item"><h4>{CHECKS[flag.check]}</h4><p>{escape(flag.concern)}</p>{quote}</div>')
        st.html("".join(items))
    st.caption("AI review points never change the ratings.")

with tab_you:
    pairs = [
        ("Type", ASSESSMENT_TYPES[a.assessment_type]),
        ("Conditions", CONDITIONS[a.conditions]),
        ("Level and weighting", f"{LEVELS[a.level]}, {a.weighting}%"),
        ("Individual or group", "Group" if a.group else "Individual"),
        ("Intended tier", TIERS[a.intended_tier]),
        ("Stated in Canvas", CANVAS_STATED[a.tier_stated_in_canvas]),
        ("Brief provided", "Yes" if a.brief.strip() else "No"),
        ("Marking criteria provided", "Yes" if a.rubric.strip() else "No"),
    ]
    st.html('<table class="gac-review">' + "".join(
        f"<tr><th scope='row'>{escape(k)}</th><td>{escape(v)}</td></tr>" for k, v in pairs) + "</table>")

st.subheader("Keep a copy")
slug = re.sub(r"[^A-Za-z0-9]+", "-", a.title).strip("-") or "assessment"
d1, d2 = st.columns(2)
d1.download_button("Download report (Word)", to_docx(result), file_name=f"genai-check-{slug}.docx",
                   mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                   type="primary", use_container_width=True)
d2.download_button("Download record (JSON)", to_json(result), file_name=f"genai-check-{slug}.json",
                   mime="application/json", use_container_width=True)

if feedback_url:
    with st.container(border=True):
        st.markdown("**Did this rating match your judgement?** Your answers shape the final rules.")
        st.link_button("Give feedback (3 minutes)", feedback_url)

st.write("")
b1, b2 = st.columns(2)
b1.button("Edit answers", on_click=go, args=(4,), use_container_width=True)
b2.button("Start a new check", on_click=reset, use_container_width=True)

footer()
