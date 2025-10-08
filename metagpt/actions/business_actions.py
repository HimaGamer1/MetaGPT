"""Business Actions implementation for MetaGPT."""

from metagpt.actions.action import Action


class SalesAction(Action):
    """Sales-related action for business agents."""
    
    name: str = "SalesAction"
    
    def __init__(self, **kwargs):
        """Initialize SalesAction."""
        super().__init__(**kwargs)
        self.desc = "Perform sales-related tasks and activities"


class MarketingAction(Action):
    """Marketing-related action for business agents."""
    
    name: str = "MarketingAction"
    
    def __init__(self, **kwargs):
        """Initialize MarketingAction."""
        super().__init__(**kwargs)
        self.desc = "Perform marketing-related tasks and campaigns"


class SupportAction(Action):
    """Support-related action for business agents."""
    
    name: str = "SupportAction"
    
    def __init__(self, **kwargs):
        """Initialize SupportAction."""
        super().__init__(**kwargs)
        self.desc = "Provide customer support and assistance"
