"""Drive the Streamlit app end to end (rules only, no API key)."""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).resolve().parent.parent / "app.py")


@pytest.fixture
def at(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("APP_PASSWORD", raising=False)
    app = AppTest.from_file(APP, default_timeout=30)
    app.secrets["APP_PASSWORD"] = ""
    app.secrets["ANTHROPIC_API_KEY"] = ""
    return app.run()


def click(at, label):
    next(b for b in at.button if b.label == label).click().run()
    assert not at.exception, at.exception


def test_full_wizard_reaches_results(at):
    assert not at.exception
    at.selectbox(key="w_conditions").select("take_home")
    click(at, "Continue")

    # Learning outcomes are required.
    click(at, "Continue")
    assert any("learning outcomes" in e.value.lower() for e in at.error)
    at.text_area(key="w_learning_outcomes").input("LO1 Evaluate competing explanations.")
    click(at, "Continue")

    at.selectbox(key="w_intended_tier").select(1)
    click(at, "Continue")
    click(at, "Continue")  # brief and rubric are optional

    assert [h.value for h in at.header] == ["Check your answers"]
    click(at, "Run the check")
    assert [t.value for t in at.title] == ["Your assessment"]
    assert any(b.label == "Start a new check" for b in at.button)


def test_answers_survive_back_and_forth(at):
    at.text_input(key="w_title").input("HIST204 Essay")
    click(at, "Continue")
    click(at, "Back")
    assert at.text_input(key="w_title").value == "HIST204 Essay"


def test_password_gate(monkeypatch):
    app = AppTest.from_file(APP, default_timeout=30)
    app.secrets["APP_PASSWORD"] = "letmein"
    app.run()
    assert not any(b.label == "Continue" for b in app.button)
    app.text_input[0].input("wrong")
    app.button[0].click().run()
    assert app.error
    app.text_input[0].input("letmein")
    app.button[0].click().run()
    assert any(b.label == "Continue" for b in app.button)
