"""Load rules and interventions from YAML and evaluate them.

The format is documented in docs/RULES.md.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

from .models import (
    CHECKS,
    RATING_ORDER,
    RATINGS,
    AssessmentInput,
    Finding,
)

CONFIG_DIR = Path(__file__).resolve().parent.parent / "config"

OPERATORS = {"not", "min", "max", "contains_any", "contains_all", "empty"}


class RulesError(ValueError):
    """The rules or interventions file is malformed."""


@dataclass
class Intervention:
    id: str
    title: str
    text: str
    placeholder: bool = False


@dataclass
class RuleSet:
    version: str
    rules: list[dict]
    interventions: dict[str, Intervention]


# ---- Loading ------------------------------------------------------------


def load(config_dir: Path = CONFIG_DIR) -> RuleSet:
    rules_doc = _read_yaml(config_dir / "rules.yaml")
    int_doc = _read_yaml(config_dir / "interventions.yaml")

    interventions = {}
    for i, item in enumerate(int_doc.get("interventions") or []):
        for key in ("id", "title", "text"):
            if not item.get(key):
                raise RulesError(f"interventions.yaml item {i + 1}: missing '{key}'")
        if item["id"] in interventions:
            raise RulesError(f"interventions.yaml: duplicate id {item['id']}")
        interventions[item["id"]] = Intervention(
            id=item["id"],
            title=str(item["title"]).strip(),
            text=" ".join(str(item["text"]).split()),
            placeholder=bool(item.get("placeholder", False)),
        )

    rules = rules_doc.get("rules") or []
    known_fields = set(AssessmentInput.__dataclass_fields__) | {
        "has_brief",
        "has_rubric",
        "has_evidence_requirement",
    }
    seen = set()
    for i, rule in enumerate(rules):
        where = f"rules.yaml rule {i + 1} ({rule.get('id', 'no id')})"
        for key in ("id", "check", "when", "rating", "why"):
            if key not in rule:
                raise RulesError(f"{where}: missing '{key}'")
        if rule["id"] in seen:
            raise RulesError(f"{where}: duplicate id")
        seen.add(rule["id"])
        if rule["check"] not in CHECKS:
            raise RulesError(f"{where}: check must be one of {list(CHECKS)}")
        if rule["rating"] not in RATINGS:
            raise RulesError(f"{where}: rating must be one of {list(RATINGS)}")
        if not isinstance(rule["when"], dict) or not rule["when"]:
            raise RulesError(f"{where}: 'when' must list at least one condition")
        for field_name, cond in rule["when"].items():
            if field_name not in known_fields:
                raise RulesError(f"{where}: unknown field '{field_name}'")
            if isinstance(cond, dict):
                bad = set(cond) - OPERATORS
                if bad:
                    raise RulesError(f"{where}: unknown operator(s) {sorted(bad)}")
            if field_name not in BOOLEAN_FIELDS and _has_bool(cond):
                raise RulesError(
                    f"{where}: '{field_name}' has a true/false value. "
                    'If you meant the answer "yes" or "no", put it in quotes.'
                )
        for iid in rule.get("interventions") or []:
            if iid not in interventions:
                raise RulesError(f"{where}: unknown intervention '{iid}'")
        st = rule.get("suggest_tier")
        if st is not None and st not in (1, 2, 3, 4):
            raise RulesError(f"{where}: suggest_tier must be 1-4")

    return RuleSet(
        version=str(rules_doc.get("version", "unversioned")),
        rules=rules,
        interventions=interventions,
    )


BOOLEAN_FIELDS = {"group", "psrb", "has_brief", "has_rubric", "has_evidence_requirement"}


def _has_bool(cond) -> bool:
    if isinstance(cond, bool):
        return True
    if isinstance(cond, list):
        return any(isinstance(v, bool) for v in cond)
    if isinstance(cond, dict):
        return any(_has_bool(v) for k, v in cond.items() if k != "empty")
    return False


def _read_yaml(path: Path) -> dict:
    try:
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
    except yaml.YAMLError as e:
        raise RulesError(f"{path.name} is not valid YAML: {e}") from e
    if not isinstance(data, dict):
        raise RulesError(f"{path.name} must be a mapping at the top level")
    return data


# ---- Evaluation ---------------------------------------------------------


def matches(cond, value) -> bool:
    """Test one condition against one fact value."""
    if isinstance(cond, dict):
        ok = True
        if "not" in cond:
            excluded = cond["not"] if isinstance(cond["not"], list) else [cond["not"]]
            ok &= value not in excluded
        if "min" in cond:
            ok &= value is not None and value >= cond["min"]
        if "max" in cond:
            ok &= value is not None and value <= cond["max"]
        if "contains_any" in cond:
            ok &= bool(set(value or []) & set(cond["contains_any"]))
        if "contains_all" in cond:
            ok &= set(cond["contains_all"]) <= set(value or [])
        if "empty" in cond:
            is_empty = not value or (isinstance(value, str) and not value.strip())
            ok &= is_empty == bool(cond["empty"])
        return ok
    if isinstance(cond, list):
        return value in cond
    return value == cond


def rule_fires(rule: dict, facts: dict) -> bool:
    return all(matches(cond, facts.get(f)) for f, cond in rule["when"].items())


def evaluate(assessment: AssessmentInput, ruleset: RuleSet):
    """Return (ratings, findings, suggested_tiers)."""
    facts = assessment.facts()
    findings: list[Finding] = []
    for rule in ruleset.rules:
        if rule_fires(rule, facts):
            findings.append(
                Finding(
                    rule_id=rule["id"],
                    check=rule["check"],
                    rating=rule["rating"],
                    why=" ".join(str(rule["why"]).split()),
                    policy=str(rule.get("policy", "")).strip(),
                    ofs=" ".join(str(rule.get("ofs", "")).split()),
                    placeholder=bool(rule.get("placeholder", False)),
                    interventions=list(rule.get("interventions") or []),
                    suggest_tier=rule.get("suggest_tier"),
                )
            )

    ratings = {check: "green" for check in CHECKS}
    for f in findings:
        if RATING_ORDER[f.rating] > RATING_ORDER[ratings[f.check]]:
            ratings[f.check] = f.rating

    suggested = sorted(
        {f.suggest_tier for f in findings if f.suggest_tier and f.suggest_tier != assessment.intended_tier}
    )
    return ratings, findings, suggested


def overall_rating(ratings: dict) -> str:
    return max(ratings.values(), key=lambda r: RATING_ORDER[r])
