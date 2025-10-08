#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/12 00:30
@Author  : alexanderwu
@File    : team.py
@Modified By: mashenquan, 2023/11/27. Add an archiving operation after completing the project, as specified in
        Section 2.2.3.3 of RFC 135.
"""
import warnings
from pathlib import Path
from typing import Any, Optional
from pydantic import BaseModel, ConfigDict, Field
from metagpt.const import SERDESER_PATH
from metagpt.context import Context
from metagpt.environment import Environment
from metagpt.environment.mgx.mgx_env import MGXEnv
from metagpt.logs import logger
from metagpt.roles import Role
from metagpt.schema import Message
from metagpt.utils.common import (
    NoMoneyException,
    read_json_file,
    serialize_decorator,
    write_json_file,
)

class Team(BaseModel):
    """
    Team: Possesses one or more roles (agents), SOP (Standard Operating Procedures), and a env for instant messaging,
    dedicated to env any multi-agent activity, such as collaboratively writing executable code.
    """
    model_config = ConfigDict(arbitrary_types_allowed=True)
    env: Optional[Environment] = None
    investment: float = Field(default=10.0)
    idea: str = Field(default="")
    use_mgx: bool = Field(default=True)

    def __init__(self, context: Context = None, **data: Any):
        super(Team, self).__init__(**data)
        ctx = context or Context()
        if not self.env and not self.use_mgx:
            self.env = Environment(context=ctx)
        elif not self.env and self.use_mgx:
            self.env = MGXEnv(context=ctx)
        else:
            self.env.context = ctx  # The `env` object is allocated by deserialization
        if "roles" in data:
            self.hire(data["roles"])
        if "env_desc" in data:
            self.env.desc = data["env_desc"]

    def serialize(self, stg_path: Path = None):
        stg_path = SERDESER_PATH.joinpath("team") if stg_path is None else stg_path
        team_info_path = stg_path.joinpath("team.json")
        serialized_data = self.model_dump()
        serialized_data["context"] = self.env.context.serialize()
        write_json_file(team_info_path, serialized_data)

    @classmethod
    def deserialize(cls, stg_path: Path, context: Context = None) -> "Team":
        """stg_path = ./storage/team"""
        # recover team_info
        team_info_path = stg_path.joinpath("team.json")
        if not team_info_path.exists():
            raise FileNotFoundError(
                "recover storage meta file `team.json` not exist, " "not to recover and please start a new project."
            )
        team_info: dict = read_json_file(team_info_path)
        ctx = context or Context()
        ctx.deserialize(team_info.pop("context", None))
        team = Team(**team_info, context=ctx)
        return team

    def hire(self, roles: list[Role]):
        """Hire roles to cooperate"""
        self.env.add_roles(roles)

    @property
    def cost_manager(self):
        """Get cost manager"""
        return self.env.context.cost_manager

    def invest(self, investment: float):
        """Invest company. raise NoMoneyException when exceed max_budget."""
        self.investment = investment
        self.cost_manager.max_budget = investment
        logger.info(f"Investment: ${investment}.")

    def _check_balance(self):
        if self.cost_manager.total_cost >= self.cost_manager.max_budget:
            raise NoMoneyException(self.cost_manager.total_cost, f"Insufficient funds: {self.cost_manager.max_budget}")

    def run_project(self, idea, send_to: str = ""):
        """Run a project from publishing user requirement."""
        self.idea = idea
        # Human requirement.
        self.env.publish_message(Message(content=idea))

    def start_project(self, idea, send_to: str = ""):
        """
        Deprecated: This method will be removed in the future.
        Please use the `run_project` method instead.
        """
        warnings.warn(
            "The 'start_project' method is deprecated and will be removed in the future. "
            "Please use the 'run_project' method instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.run_project(idea=idea, send_to=send_to)

    @serialize_decorator
    async def run(self, n_round=3, idea="", send_to="", auto_archive=True):
        """Run company until target round or no money"""
        if idea:
            self.run_project(idea=idea, send_to=send_to)
        while n_round > 0:
            if self.env.is_idle:
                logger.debug("All roles are idle.")
                break
            n_round -= 1
            self._check_balance()
            await self.env.run()
            logger.debug(f"max {n_round=} left.")
        self.env.archive(auto_archive)
        return self.env.history


# Pipeline Orchestration Classes

class TaskMessage(BaseModel):
    """Message for task communication in workflows"""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    task_id: str = Field(description="Unique identifier for the task")
    task_type: str = Field(description="Type of task (e.g., 'finance', 'hr', 'legal')")
    content: str = Field(description="Task content/description")
    sender: str = Field(description="Task sender role/agent")
    recipient: Optional[str] = Field(default=None, description="Task recipient role/agent")
    priority: int = Field(default=0, description="Task priority level")
    metadata: dict = Field(default_factory=dict, description="Additional task metadata")
    

class WorkflowOrchestrator(BaseModel):
    """Orchestrates multi-agent workflows and task pipelines"""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    team: Optional[Team] = Field(default=None, description="Team instance to orchestrate")
    task_queue: list[TaskMessage] = Field(default_factory=list, description="Queue of pending tasks")
    completed_tasks: list[TaskMessage] = Field(default_factory=list, description="List of completed tasks")
    active_workflows: dict[str, list[TaskMessage]] = Field(default_factory=dict, description="Active workflow instances")
    
    def __init__(self, team: Team = None, **data: Any):
        super().__init__(**data)
        if team:
            self.team = team
    
    def create_task(self, task_type: str, content: str, sender: str, 
                   recipient: Optional[str] = None, priority: int = 0, 
                   metadata: Optional[dict] = None) -> TaskMessage:
        """Create a new task message"""
        import uuid
        task_id = str(uuid.uuid4())
        task = TaskMessage(
            task_id=task_id,
            task_type=task_type,
            content=content,
            sender=sender,
            recipient=recipient,
            priority=priority,
            metadata=metadata or {}
        )
        return task
    
    def add_task(self, task: TaskMessage) -> None:
        """Add task to queue"""
        self.task_queue.append(task)
        self.task_queue.sort(key=lambda t: t.priority, reverse=True)
        logger.info(f"Task {task.task_id} added to queue (priority: {task.priority})")
    
    def get_next_task(self) -> Optional[TaskMessage]:
        """Get next task from queue"""
        if self.task_queue:
            return self.task_queue.pop(0)
        return None
    
    def complete_task(self, task: TaskMessage) -> None:
        """Mark task as completed"""
        self.completed_tasks.append(task)
        logger.info(f"Task {task.task_id} completed")
    
    def create_workflow(self, workflow_id: str, tasks: list[TaskMessage]) -> None:
        """Create a new workflow with multiple tasks"""
        self.active_workflows[workflow_id] = tasks
        for task in tasks:
            self.add_task(task)
        logger.info(f"Workflow {workflow_id} created with {len(tasks)} tasks")
    
    def get_workflow_status(self, workflow_id: str) -> dict:
        """Get status of a workflow"""
        if workflow_id not in self.active_workflows:
            return {"status": "not_found"}
        
        workflow_tasks = self.active_workflows[workflow_id]
        completed = [t for t in workflow_tasks if t in self.completed_tasks]
        pending = [t for t in workflow_tasks if t in self.task_queue]
        
        return {
            "status": "active",
            "total_tasks": len(workflow_tasks),
            "completed": len(completed),
            "pending": len(pending),
            "progress": len(completed) / len(workflow_tasks) if workflow_tasks else 0
        }
    
    async def execute_workflow(self, workflow_id: str) -> dict:
        """Execute a workflow and return results"""
        if workflow_id not in self.active_workflows:
            return {"error": "Workflow not found"}
        
        results = []
        while True:
            task = self.get_next_task()
            if not task:
                break
            
            # Execute task (stub implementation)
            logger.info(f"Executing task {task.task_id}: {task.content}")
            result = {"task_id": task.task_id, "status": "completed", "result": "Task executed"}
            results.append(result)
            
            self.complete_task(task)
        
        return {
            "workflow_id": workflow_id,
            "status": "completed",
            "results": results
        }
