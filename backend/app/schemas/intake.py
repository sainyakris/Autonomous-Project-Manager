from typing import Literal

from pydantic import BaseModel, Field, model_validator

class Question(BaseModel):
    id: str
    category: Literal["scope", "team", "timeline", "technology", "budget", "quality", "constraints"]
    question: str = Field(min_length=5, max_length=300)
    why_important: str = Field(max_length=300)
    required: bool = True


class Analysis(BaseModel):
    clarity_score: float = Field(ge=0.0, le=1.0)
    summary: str = Field(max_length=500)
    what_is_missing: list[str] = Field(default_factory=list)
    questions: list[Question] = Field(default_factory=list, max_length=5)


class PlanTask(BaseModel):
    key: str = Field(min_length=1, max_length=20)  # temporary id like "t1", only meaningful inside this plan
    title: str = Field(min_length=3, max_length=300)
    description: str = Field(max_length=2000)
    priority: Literal["low", "medium", "high", "critical"]
    estimated_hours: float = Field(gt=0, le=80)
    depends_on: list[str] = Field(default_factory=list)


class Plan(BaseModel):
    summary: str = Field(max_length=1000)
    risk_level: Literal["low", "medium", "high"]
    tasks: list[PlanTask] = Field(min_length=3, max_length=30)

    @model_validator(mode="after")
    def check_dependency_graph(self) -> "Plan":
        keys = [t.key for t in self.tasks]
        if len(set(keys)) != len(keys):
            raise ValueError("task keys must be unique")
        known = set(keys)

        for t in self.tasks:
            if len(set(t.depends_on)) != len(t.depends_on):
                raise ValueError(f"task {t.key} lists the same dependency twice")
            for dep in t.depends_on:
                if dep == t.key:
                    raise ValueError(f"task {t.key} depends on itself")
                if dep not in known:
                    raise ValueError(f"task {t.key} depends on unknown task {dep}")

        # Cycle check (Kahn's algorithm): repeatedly remove tasks with no
        # unfinished dependencies. If some tasks can never be removed, there's a cycle.
        indegree = {t.key: len(t.depends_on) for t in self.tasks}
        dependents: dict[str, list[str]] = {k: [] for k in known}
        for t in self.tasks:
            for dep in t.depends_on:
                dependents[dep].append(t.key)

        ready = [k for k, n in indegree.items() if n == 0]
        visited = 0
        while ready:
            k = ready.pop()
            visited += 1
            for d in dependents[k]:
                indegree[d] -= 1
                if indegree[d] == 0:
                    ready.append(d)

        if visited != len(keys):
            raise ValueError("dependencies contain a cycle")
        return self