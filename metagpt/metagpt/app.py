#!/usr/bin/env python3
from __future__ import annotations

"""
Simple backend example for user/company registry and agent workflow linking.
Framework-agnostic core with a minimal FastAPI app for demonstration.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional

try:
    from fastapi import FastAPI, HTTPException
    from pydantic import BaseModel, EmailStr
except Exception:  # FastAPI not installed: allow importing the module without runtime deps
    FastAPI = None  # type: ignore
    BaseModel = object  # type: ignore
    EmailStr = str  # type: ignore


# In-memory store (replace with real DB; see db/schema.sql)
USERS: Dict[int, dict] = {}
COMPANIES: Dict[int, dict] = {}
AGENTS: Dict[int, dict] = {}
WORKFLOWS: Dict[int, dict] = {}

_id_seq = {"user": 0, "company": 0, "agent": 0, "workflow": 0}

def _next_id(kind: str) -> int:
    _id_seq[kind] += 1
    return _id_seq[kind]


@dataclass
class User:
    email: str
    name: str
    company_id: Optional[int] = None
    id: int = field(default_factory=lambda: _next_id("user"))
    created_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "email": self.email,
            "name": self.name,
            "company_id": self.company_id,
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class Company:
    name: str
    domain: Optional[str] = None
    id: int = field(default_factory=lambda: _next_id("company"))
    created_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "domain": self.domain,
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class Agent:
    name: str
    profile: str
    company_id: int
    id: int = field(default_factory=lambda: _next_id("agent"))

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "profile": self.profile,
            "company_id": self.company_id,
        }


@dataclass
class Workflow:
    name: str
    agent_ids: List[int]
    company_id: int
    id: int = field(default_factory=lambda: _next_id("workflow"))
    created_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "agent_ids": self.agent_ids,
            "company_id": self.company_id,
            "created_at": self.created_at.isoformat(),
        }


# Core API (can be reused in CLI/tests)

def register_company(name: str, domain: Optional[str] = None) -> dict:
    company = Company(name=name, domain=domain)
    COMPANIES[company.id] = company.to_dict()
    return COMPANIES[company.id]


def register_user(name: str, email: str, company_id: Optional[int] = None) -> dict:
    if company_id and company_id not in COMPANIES:
        raise ValueError("company_id not found")
    user = User(name=name, email=email, company_id=company_id)
    USERS[user.id] = user.to_dict()
    return USERS[user.id]


def create_agent(name: str, profile: str, company_id: int) -> dict:
    if company_id not in COMPANIES:
        raise ValueError("company_id not found")
    agent = Agent(name=name, profile=profile, company_id=company_id)
    AGENTS[agent.id] = agent.to_dict()
    return AGENTS[agent.id]


def create_workflow(name: str, agent_ids: List[int], company_id: int) -> dict:
    for aid in agent_ids:
        if aid not in AGENTS:
            raise ValueError(f"agent_id {aid} not found")
        if AGENTS[aid]["company_id"] != company_id:
            raise ValueError("agent/company mismatch")
    wf = Workflow(name=name, agent_ids=agent_ids, company_id=company_id)
    WORKFLOWS[wf.id] = wf.to_dict()
    return WORKFLOWS[wf.id]


# Optional FastAPI app
if FastAPI:
    app = FastAPI(title="MetaGPT Backend Example")

    class CompanyIn(BaseModel):
        name: str
        domain: Optional[str] = None

    class UserIn(BaseModel):
        name: str
        email: EmailStr
        company_id: Optional[int] = None

    class AgentIn(BaseModel):
        name: str
        profile: str
        company_id: int

    class WorkflowIn(BaseModel):
        name: str
        agent_ids: List[int]
        company_id: int

    @app.post("/companies")
    def api_register_company(payload: CompanyIn):
        return register_company(payload.name, payload.domain)

    @app.post("/users")
    def api_register_user(payload: UserIn):
        try:
            return register_user(payload.name, payload.email, payload.company_id)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    @app.post("/agents")
    def api_create_agent(payload: AgentIn):
        try:
            return create_agent(payload.name, payload.profile, payload.company_id)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    @app.post("/workflows")
    def api_create_workflow(payload: WorkflowIn):
        try:
            return create_workflow(payload.name, payload.agent_ids, payload.company_id)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))


if __name__ == "__main__":
    # Quick demo run (without FastAPI)
    acme = register_company("Acme Corp", domain="acme.com")
    alice = register_user("Alice", "alice@acme.com", company_id=acme["id"])
    bob = register_user("Bob", "bob@acme.com", company_id=acme["id"])

    pm = create_agent("Product Manager", "Product", acme["id"])
    mk = create_agent("Marketing Manager", "Marketing", acme["id"])
    sl = create_agent("Sales Manager", "Sales", acme["id"])
    sp = create_agent("Support Manager", "Support", acme["id"])

    wf = create_workflow(
        name="Product Launch",
        agent_ids=[pm["id"], mk["id"], sl["id"], sp["id"]],
        company_id=acme["id"],
    )

    print({
        "company": acme,
        "users": [alice, bob],
        "agents": [pm, mk, sl, sp],
        "workflow": wf,
    })
