from app.api.routes import projects as project_routes
from app.schemas.intake import Analysis, Plan, PlanTask, Question
from app.services.llm import LLMError

BRIEF = {"name": "Fitness App", "description": "A mobile app for tracking workouts and progress."}


async def auth_for(client, email="sai@example.com"):
    await client.post(
        "/api/v1/auth/register",
        json={"email": email, "name": "Sai", "password": "password123"},
    )
    r = await client.post("/api/v1/auth/login", json={"email": email, "password": "password123"})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def canned_plan() -> Plan:
    def t(key, title, deps):
        return PlanTask(key=key, title=title, description="d", priority="high",
                        estimated_hours=4, depends_on=deps)

    return Plan(
        summary="A plan", risk_level="medium",
        tasks=[t("t1", "Design schema", []), t("t2", "Write API", ["t1"]), t("t3", "Build UI", ["t1", "t2"])],
    )


def fake_analysis(score: float) -> Analysis:
    return Analysis(
        clarity_score=score, summary="s", what_is_missing=["platform"],
        questions=[Question(id="q1", category="scope", question="Which platforms?", why_important="x")],
    )


async def test_analyze_low_clarity_not_ready(client, monkeypatch):
    async def fake(name, description):
        return fake_analysis(0.2)

    monkeypatch.setattr(project_routes, "analyze_brief", fake)
    r = await client.post("/api/v1/projects/analyze", json=BRIEF, headers=await auth_for(client))
    assert r.status_code == 200
    assert r.json()["ready"] is False
    assert len(r.json()["questions"]) == 1


async def test_analyze_high_clarity_ready(client, monkeypatch):
    async def fake(name, description):
        return fake_analysis(0.9)

    monkeypatch.setattr(project_routes, "analyze_brief", fake)
    r = await client.post("/api/v1/projects/analyze", json=BRIEF, headers=await auth_for(client))
    assert r.json()["ready"] is True


async def test_create_saves_real_dependency_links(client, monkeypatch):
    async def fake(name, description, answers):
        return canned_plan()

    monkeypatch.setattr(project_routes, "generate_plan", fake)
    r = await client.post(
        "/api/v1/projects",
        json={**BRIEF, "answers": {"Which platforms?": "iOS and Android"}},
        headers=await auth_for(client),
    )
    assert r.status_code == 201
    tasks = r.json()["tasks"]
    assert [t["title"] for t in tasks] == ["Design schema", "Write API", "Build UI"]  # order kept

    ids = {t["id"] for t in tasks}
    by_title = {t["title"]: t for t in tasks}
    for t in tasks:
        for dep in t["depends_on"]:
            assert dep in ids and len(dep) == 36  # a real UUID, not "t1"
    assert by_title["Write API"]["depends_on"] == [by_title["Design schema"]["id"]]
    assert set(by_title["Build UI"]["depends_on"]) == {
        by_title["Design schema"]["id"], by_title["Write API"]["id"]
    }


async def test_create_saves_nothing_when_ai_fails(client, monkeypatch):
    async def fake(name, description, answers):
        raise LLMError("boom")

    monkeypatch.setattr(project_routes, "generate_plan", fake)
    headers = await auth_for(client)
    r = await client.post("/api/v1/projects", json=BRIEF, headers=headers)
    assert r.status_code == 502
    assert (await client.get("/api/v1/projects", headers=headers)).json() == []


async def test_users_cannot_see_each_others_projects(client, monkeypatch):
    async def fake(name, description, answers):
        return canned_plan()

    monkeypatch.setattr(project_routes, "generate_plan", fake)
    alice = await auth_for(client, "alice@example.com")
    bob = await auth_for(client, "bob@example.com")
    project_id = (await client.post("/api/v1/projects", json=BRIEF, headers=alice)).json()["id"]

    assert (await client.get(f"/api/v1/projects/{project_id}", headers=alice)).status_code == 200
    assert (await client.get(f"/api/v1/projects/{project_id}", headers=bob)).status_code == 404
    assert (await client.get("/api/v1/projects", headers=bob)).json() == []


async def test_projects_require_auth(client):
    r = await client.get("/api/v1/projects")
    assert r.status_code in (401, 403)