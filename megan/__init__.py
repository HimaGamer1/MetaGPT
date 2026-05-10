"""Megan — multi-agent framework.

Megan is a multi-agent software-company framework. The runtime is the
unmodified upstream agent framework that lives in :mod:`metagpt`; this top
level package re-exports the public surface under the Megan brand so that
users can write ``from megan import Team`` etc.

The framework code is intentionally left untouched so behaviour matches the
underlying agent runtime exactly.
"""

from metagpt import _compat as _  # noqa: F401
from metagpt.actions import Action  # noqa: F401
from metagpt.config2 import Config, config  # noqa: F401
from metagpt.context import Context  # noqa: F401
from metagpt.roles import (  # noqa: F401
    Architect,
    DataAnalyst,
    Engineer2,
    ProductManager,
    ProjectManager,
    QaEngineer,
    Role,
    TeamLeader,
)
from metagpt.schema import Message  # noqa: F401
from metagpt.software_company import generate_repo  # noqa: F401
from metagpt.team import Team  # noqa: F401

__all__ = [
    "Action",
    "Architect",
    "Config",
    "Context",
    "DataAnalyst",
    "Engineer2",
    "Message",
    "ProductManager",
    "ProjectManager",
    "QaEngineer",
    "Role",
    "Team",
    "TeamLeader",
    "config",
    "generate_repo",
]

__brand__ = "Megan"
__tagline__ = "Multi-Agent Software Company Framework"
