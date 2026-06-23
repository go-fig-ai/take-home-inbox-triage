"""Acceptance-criteria suite for the Inbox Triage skill.

This suite IS the spec for the non-negotiable parts of the task. It is red
against the stub and goes green when the skill is built correctly.

The deterministic tests (routing, the human-in-the-loop gate, least privilege)
run offline — no model, no network — by injecting a fake classifier and a spy
client. The one test that exercises real classification is opt-in: set
RUN_AI_TESTS=1 to run it (it needs your ANTHROPIC_API_KEY and the mock API).

Add at least one meaningful test of your own before you submit.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from src.triage_skill import (
    ACTION_KINDS,
    LABELS,
    ProposedAction,
    classify_email,
    execute,
    plan_actions,
    triage_inbox,
)

FIXTURES = json.loads((Path(__file__).resolve().parent.parent / "fixtures" / "emails.json").read_text())
BY_ID = {e["id"]: e for e in FIXTURES}


# --------------------------------------------------------------------------- #
# Test doubles
# --------------------------------------------------------------------------- #
class SpyClient:
    """Records every write call without touching the network."""

    def __init__(self):
        self.calls: list[tuple[str, dict]] = []

    def get_inbox(self):
        return FIXTURES

    def send_reply(self, **kw):
        self.calls.append(("send_reply", kw))
        return {"status": "sent", **kw}

    def create_contact(self, **kw):
        self.calls.append(("create_contact", kw))
        return {"status": "created", **kw}

    def create_deal(self, **kw):
        self.calls.append(("create_deal", kw))
        return {"status": "created", **kw}


def _reply_action():
    return ProposedAction(
        kind="send_reply",
        payload={"to": "x@example.com", "subject": "re", "body": "hi"},
    )


# --------------------------------------------------------------------------- #
# Routing table
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("label", ["billing", "bug_report"])
def test_transactional_labels_reply_only(label):
    actions = plan_actions(label, BY_ID["e-001"])
    kinds = [a.kind for a in actions]
    assert kinds == ["send_reply"]


def test_sales_lead_replies_and_creates_crm_records():
    actions = plan_actions("sales_lead", BY_ID["e-003"])
    kinds = {a.kind for a in actions}
    assert kinds == {"send_reply", "create_contact", "create_deal"}


def test_spam_plans_no_actions():
    assert plan_actions("spam", BY_ID["e-004"]) == []


def test_planned_action_kinds_are_valid():
    for label in ("billing", "bug_report", "sales_lead"):
        for action in plan_actions(label, BY_ID["e-001"]):
            assert action.kind in ACTION_KINDS


# --------------------------------------------------------------------------- #
# Human-in-the-loop gate  (the security heart of the task)
# --------------------------------------------------------------------------- #
def test_gate_blocks_unapproved_action():
    spy = SpyClient()
    result = execute(_reply_action(), spy, approved=False)
    assert result is None
    assert spy.calls == [], "an unapproved action must not touch the outside world"


def test_gate_executes_approved_action():
    spy = SpyClient()
    action = _reply_action()
    result = execute(action, spy, approved=True)
    assert result is not None
    assert len(spy.calls) == 1
    name, kw = spy.calls[0]
    assert name == "send_reply"
    assert kw == action.payload


# --------------------------------------------------------------------------- #
# Orchestration honours the approver  (least privilege + HITL end to end)
# --------------------------------------------------------------------------- #
def _fake_classifier_from(labels: dict[str, str]):
    return lambda email: labels[email["id"]]


def test_orchestration_makes_no_writes_when_approver_rejects_all():
    spy = SpyClient()
    classifier = _fake_classifier_from({e["id"]: "sales_lead" for e in FIXTURES})
    triage_inbox(spy, approver=lambda email, action: False, classifier=classifier)
    assert spy.calls == [], "rejecting every proposal must produce zero side effects"


def test_orchestration_executes_only_approved_non_spam():
    spy = SpyClient()
    # One of each so spam's no-op path is exercised alongside a writing path.
    labels = {
        "e-001": "billing",
        "e-002": "bug_report",
        "e-003": "sales_lead",
        "e-004": "spam",
        "e-005": "billing",
        "e-006": "bug_report",
        "e-007": "spam",
        "e-008": "sales_lead",
    }
    triage_inbox(spy, approver=lambda email, action: True, classifier=_fake_classifier_from(labels))

    kinds = [name for name, _ in spy.calls]
    # 4 transactional replies + 2 leads (reply+contact+deal each) = 4 + 6
    assert kinds.count("send_reply") == 6
    assert kinds.count("create_contact") == 2
    assert kinds.count("create_deal") == 2
    # spam produced nothing
    assert len(spy.calls) == 10


# --------------------------------------------------------------------------- #
# Live classification — opt in with RUN_AI_TESTS=1
# --------------------------------------------------------------------------- #
@pytest.mark.skipif(
    os.environ.get("RUN_AI_TESTS") != "1",
    reason="set RUN_AI_TESTS=1 to exercise real classification",
)
def test_classify_returns_a_valid_label_for_every_fixture():
    for email in FIXTURES:
        assert classify_email(email) in LABELS
