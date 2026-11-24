"""Data structures for one assessment check.

Field names here are the names rules use in `config/rules.yaml` under `when:`.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Optional

# ---- Choice lists (value -> label shown to staff) ------------------------

ASSESSMENT_TYPES = {
    "essay": "Essay",
    "report": "Report",
    "dissertation": "Dissertation or project report",
    "reflective": "Reflective writing",
    "exam": "Exam",
    "short_answer_quiz": "Short-answer or MCQ test",
    "presentation": "Presentation",
    "portfolio": "Portfolio",
    "code": "Code or software",
    "practical": "Practical, lab or clinical skill",
    "oral": "Viva or oral examination",
    "other": "Other",
}

CONDITIONS = {
    "invigilated": "Invigilated exam",
    "supervised_in_class": "Supervised in class (not a formal exam)",
    "live_oral": "Live or oral (in person or real-time online)",
    "timed_online_unsupervised": "Timed online, unsupervised",
    "take_home": "Take-home / coursework",
}

LEVELS = {
    3: "Level 3 (foundation)",
    4: "Level 4",
    5: "Level 5",
    6: "Level 6",
    7: "Level 7 (taught postgraduate)",
}

TIERS = {
    1: "Tier 1: Prohibited (no AI use)",
    2: "Tier 2: Contextual support (limited / assistive use)",
    3: "Tier 3: Structural scaffold (exploratory / critical use)",
    4: "Tier 4: Integrated (integral / embedded use)",
}

CANVAS_STATED = {
    "yes": "Yes",
    "no": "No",
    "not_sure": "Not sure",
}

EVIDENCE_TYPES = {
    "declaration": "Declaration of AI use",
    "interaction_log": "Record of key AI interactions (summary of use)",
    "prompts_outputs": "Prompts and outputs",
    "drafts_edits": "Drafts or edit history",
    "critical_evaluation": "Critical evaluation of AI contributions",
    "reflection": "Reflection on ethics, bias or accuracy",
}

RATINGS = ("green", "amber", "red")
RATING_ORDER = {"green": 0, "amber": 1, "red": 2}
RATING_LABELS = {"green": "Green", "amber": "Amber", "red": "Red"}

CHECKS = {
    "secure": "Secure",
    "tier": "Tier-appropriate",
    "valid": "Valid",
    "reliable": "Reliable",
}


# ---- Input --------------------------------------------------------------


@dataclass
class AssessmentInput:
    assessment_type: str
    conditions: str
    level: int
    weighting: int
    group: bool
    learning_outcomes: str
    intended_tier: int
    tier_stated_in_canvas: str
    evidence_required: list[str] = field(default_factory=list)
    rubric: str = ""
    brief: str = ""
    psrb: bool = False
    psrb_details: str = ""
    title: str = ""

    def validate(self) -> list[str]:
        """Return a list of problems; empty means valid."""
        problems = []
        if self.assessment_type not in ASSESSMENT_TYPES:
            problems.append(f"Unknown assessment type: {self.assessment_type}")
        if self.conditions not in CONDITIONS:
            problems.append(f"Unknown conditions: {self.conditions}")
        if self.level not in LEVELS:
            problems.append(f"Unknown level: {self.level}")
        if not 0 <= self.weighting <= 100:
            problems.append("Weighting must be between 0 and 100")
        if self.intended_tier not in TIERS:
            problems.append(f"Unknown tier: {self.intended_tier}")
        if self.tier_stated_in_canvas not in CANVAS_STATED:
            problems.append(f"Unknown Canvas answer: {self.tier_stated_in_canvas}")
        for e in self.evidence_required:
            if e not in EVIDENCE_TYPES:
                problems.append(f"Unknown evidence type: {e}")
        if not self.learning_outcomes.strip():
            problems.append("Learning outcomes are required")
        return problems

    def facts(self) -> dict:
        """Values rules can test, including derived ones."""
        d = asdict(self)
        d["has_brief"] = bool(self.brief.strip())
        d["has_rubric"] = bool(self.rubric.strip())
        d["has_evidence_requirement"] = bool(self.evidence_required)
        return d

    @classmethod
    def from_dict(cls, data: dict) -> "AssessmentInput":
        known = {f for f in cls.__dataclass_fields__}
        return cls(**{k: v for k, v in data.items() if k in known})


# ---- Output -------------------------------------------------------------


@dataclass
class Finding:
    rule_id: str
    check: str
    rating: str
    why: str
    policy: str
    ofs: str
    placeholder: bool
    interventions: list[str]
    suggest_tier: Optional[int] = None


@dataclass
class Recommendation:
    intervention_id: str
    title: str
    text: str  # standard wording, or tailored wording when AI ran
    tailored: bool
    triggered_by: list[str]


@dataclass
class AIFlag:
    check: str
    concern: str
    evidence: str


@dataclass
class Result:
    input: AssessmentInput
    ratings: dict  # check -> rating
    overall: str
    findings: list[Finding]
    recommendations: list[Recommendation]
    suggested_tiers: list[int]
    confidence: str  # high / medium / low
    confidence_reason: str
    ai_ran: bool
    ai_note: str
    ai_flags: list[AIFlag]
    rules_version: str
    uses_placeholder_rules: bool
    generated_at: str

    def to_dict(self) -> dict:
        return asdict(self)
