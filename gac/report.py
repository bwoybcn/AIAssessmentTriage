"""Build the downloadable Word report and JSON record."""

from __future__ import annotations

import io
import json

from docx import Document
from docx.shared import Pt

from . import ADVISORY_NOTE, APP_NAME, OFS_NOTE
from .models import (
    ASSESSMENT_TYPES,
    CANVAS_STATED,
    CHECKS,
    CONDITIONS,
    EVIDENCE_TYPES,
    LEVELS,
    RATING_LABELS,
    TIERS,
    Result,
)


def to_json(result: Result) -> bytes:
    data = {"app": APP_NAME, "advisory_note": ADVISORY_NOTE, **result.to_dict()}
    return json.dumps(data, indent=2, ensure_ascii=False).encode("utf-8")


def to_docx(result: Result) -> bytes:
    a = result.input
    doc = Document()
    style = doc.styles["Normal"]
    style.font.name = "Arial"
    style.font.size = Pt(11)
    doc.core_properties.title = f"{APP_NAME}: {a.title or 'assessment'}"

    doc.add_heading(APP_NAME, level=0)
    doc.add_paragraph(f"Assessment: {a.title or '(untitled)'}")
    doc.add_paragraph(f"Generated: {result.generated_at}. Rules version: {result.rules_version}.")
    doc.add_paragraph(ADVISORY_NOTE)
    if result.uses_placeholder_rules:
        doc.add_paragraph(
            "Prototype: these results use placeholder rules that have not been approved."
        )

    doc.add_heading("Summary", level=1)
    doc.add_paragraph(f"Overall rating: {RATING_LABELS[result.overall]}")
    table = doc.add_table(rows=1, cols=2)
    table.style = "Table Grid"
    hdr = table.rows[0].cells
    hdr[0].text, hdr[1].text = "Check", "Rating"
    for check, label in CHECKS.items():
        row = table.add_row().cells
        row[0].text, row[1].text = label, RATING_LABELS[result.ratings[check]]
    doc.add_paragraph(f"Confidence: {result.confidence.capitalize()}. {result.confidence_reason}")
    if result.suggested_tiers:
        tiers = ", ".join(TIERS[t] for t in result.suggested_tiers)
        doc.add_paragraph(f"Tier to consider instead of Tier {a.intended_tier}: {tiers}")

    doc.add_heading("Findings", level=1)
    if not result.findings:
        doc.add_paragraph("The current rules found no concerns.")
    for f in result.findings:
        doc.add_heading(f"{CHECKS[f.check]}: {RATING_LABELS[f.rating]} ({f.rule_id})", level=2)
        doc.add_paragraph(f.why)
        if f.policy:
            doc.add_paragraph(f"University policy: section {f.policy}")
        if f.ofs:
            doc.add_paragraph(f"OfS: {f.ofs}")

    doc.add_heading("Points raised by AI review", level=1)
    doc.add_paragraph(result.ai_note)
    for flag in result.ai_flags:
        p = doc.add_paragraph(style="List Bullet")
        p.add_run(f"{CHECKS[flag.check]}: ").bold = True
        p.add_run(flag.concern)
        if flag.evidence:
            p.add_run(f' (from: "{flag.evidence}")')
    doc.add_paragraph("These points do not change the ratings.")

    doc.add_heading("Recommendations", level=1)
    if not result.recommendations:
        doc.add_paragraph("No changes recommended by the current rules.")
    for r in result.recommendations:
        doc.add_heading(r.title, level=2)
        doc.add_paragraph(r.text)

    doc.add_heading("What you entered", level=1)
    rows = [
        ("Assessment type", ASSESSMENT_TYPES[a.assessment_type]),
        ("Conditions", CONDITIONS[a.conditions]),
        ("Level", LEVELS[a.level]),
        ("Weighting", f"{a.weighting}%"),
        ("Group work", "Yes" if a.group else "No"),
        ("Intended tier", TIERS[a.intended_tier]),
        ("Tier stated in Canvas", CANVAS_STATED[a.tier_stated_in_canvas]),
        (
            "AI-use evidence required",
            ", ".join(EVIDENCE_TYPES[e] for e in a.evidence_required) or "None",
        ),
        ("PSRB or fitness-to-practise constraints", "Yes" if a.psrb else "No"),
    ]
    t = doc.add_table(rows=0, cols=2)
    t.style = "Table Grid"
    for k, v in rows:
        c = t.add_row().cells
        c[0].text, c[1].text = k, v
    for heading, text in (
        ("Learning outcomes", a.learning_outcomes),
        ("PSRB details", a.psrb_details if a.psrb else ""),
        ("Brief", a.brief),
        ("Marking criteria", a.rubric),
    ):
        if text.strip():
            doc.add_heading(heading, level=2)
            for para in text.strip().split("\n"):
                doc.add_paragraph(para)

    doc.add_paragraph(OFS_NOTE)

    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()
