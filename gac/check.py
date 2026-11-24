"""Run one full check: rules, then (optionally) the AI step."""

from __future__ import annotations

from datetime import datetime, timezone

from . import ai
from .models import AssessmentInput, Recommendation, Result
from .rules import RuleSet, evaluate, overall_rating


def confidence(a: AssessmentInput) -> tuple[str, str]:
    has_brief, has_rubric = bool(a.brief.strip()), bool(a.rubric.strip())
    if has_brief and has_rubric:
        return "high", "The brief and marking criteria were both provided."
    if has_brief or has_rubric:
        missing = "marking criteria" if has_brief else "brief"
        return "medium", f"The {missing} was not provided, so some issues may be missed."
    return "low", "Neither the brief nor the marking criteria were provided, so some issues may be missed."


def run_check(a: AssessmentInput, ruleset: RuleSet, client=None) -> Result:
    problems = a.validate()
    if problems:
        raise ValueError("; ".join(problems))

    ratings, findings, suggested = evaluate(a, ruleset)

    # Recommendations in the order rules first triggered them.
    triggered: dict[str, list[str]] = {}
    for f in findings:
        for iid in f.interventions:
            triggered.setdefault(iid, []).append(f.rule_id)
    interventions = [ruleset.interventions[iid] for iid in triggered]

    ai_result, ai_note = None, "AI analysis was not run."
    if client is not None:
        ai_result, ai_note = ai.analyse(client, a, ratings, findings, interventions)

    tailored = ai_result.tailored if ai_result else {}
    recommendations = [
        Recommendation(
            intervention_id=i.id,
            title=i.title,
            text=tailored.get(i.id, i.text),
            tailored=i.id in tailored,
            triggered_by=triggered[i.id],
        )
        for i in interventions
    ]

    conf, conf_reason = confidence(a)
    return Result(
        input=a,
        ratings=ratings,
        overall=overall_rating(ratings),
        findings=findings,
        recommendations=recommendations,
        suggested_tiers=suggested,
        confidence=conf,
        confidence_reason=conf_reason,
        ai_ran=ai_result is not None,
        ai_note=ai_note,
        ai_flags=ai_result.flags if ai_result else [],
        rules_version=ruleset.version,
        uses_placeholder_rules=any(r.get("placeholder") for r in ruleset.rules)
        or any(i.placeholder for i in ruleset.interventions.values()),
        generated_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
    )
