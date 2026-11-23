import pytest
from pydantic import ValidationError

from app.schemas.intake import Plan


def task(key, depends_on=None):
    return {
        "key": key,
        "title": f"Task {key}",
        "description": "d",
        "priority": "medium",
        "estimated_hours": 4,
        "depends_on": depends_on or [],
    }


def plan(*tasks):
    return {"summary": "s", "risk_level": "low", "tasks": list(tasks)}


def test_valid_plan():
    p = Plan.model_validate(plan(task("t1"), task("t2", ["t1"]), task("t3", ["t1", "t2"])))
    assert len(p.tasks) == 3


def test_unknown_dependency_rejected():
    with pytest.raises(ValidationError, match="unknown task t9"):
        Plan.model_validate(plan(task("t1"), task("t2", ["t9"]), task("t3")))


def test_self_dependency_rejected():
    with pytest.raises(ValidationError, match="depends on itself"):
        Plan.model_validate(plan(task("t1", ["t1"]), task("t2"), task("t3")))


def test_cycle_rejected():
    with pytest.raises(ValidationError, match="cycle"):
        Plan.model_validate(plan(task("t1", ["t3"]), task("t2", ["t1"]), task("t3", ["t2"])))


def test_duplicate_keys_rejected():
    with pytest.raises(ValidationError, match="unique"):
        Plan.model_validate(plan(task("t1"), task("t1"), task("t3")))


def test_invalid_priority_rejected():
    bad = task("t1")
    bad["priority"] = "urgent"
    with pytest.raises(ValidationError):
        Plan.model_validate(plan(bad, task("t2"), task("t3")))