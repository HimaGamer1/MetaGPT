"""Business Agent implementation for MetaGPT."""

from metagpt.roles.role import Role
from typing import Optional, List


class BusinessAgent(Role):
    """BusinessAgent class that subclasses Role for business-related tasks."""

    def __init__(
        self,
        name: str = "Business Agent",
        profile: str = "Business Agent",
        goal: str = "Execute business tasks",
        constraints: Optional[str] = None,
        actions: List = None,
        **kwargs
    ):
        """Initialize BusinessAgent.
        
        Args:
            name: Name of the agent
            profile: Profile description of the agent
            goal: Goal of the agent
            constraints: Optional constraints for the agent
            actions: List of actions the agent can perform (default empty list)
        """
        if actions is None:
            actions = []
        
        super().__init__(
            name=name,
            profile=profile,
            goal=goal,
            constraints=constraints,
            actions=actions,
            **kwargs
        )


def create_custom_agent(
    name: str,
    job: str,
    goal: str,
    actions: List = None
) -> BusinessAgent:
    """Utility function to create a custom BusinessAgent.
    
    Args:
        name: Name of the agent
        job: Job/profile description of the agent
        goal: Goal of the agent
        actions: List of actions the agent can perform
    
    Returns:
        BusinessAgent: A configured BusinessAgent instance
    """
    if actions is None:
        actions = []
    
    return BusinessAgent(
        name=name,
        profile=job,
        goal=goal,
        actions=actions
    )
