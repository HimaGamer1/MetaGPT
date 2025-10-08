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


class FinanceAction(Action):
    """Finance-related action for business agents."""
    
    name: str = "FinanceAction"
    
    def __init__(self, **kwargs):
        """Initialize FinanceAction."""
        super().__init__(**kwargs)
        self.desc = "Manage financial operations, budgeting, and accounting tasks"


class HRAction(Action):
    """Human Resources action for business agents."""
    
    name: str = "HRAction"
    
    def __init__(self, **kwargs):
        """Initialize HRAction."""
        super().__init__(**kwargs)
        self.desc = "Handle human resources, recruitment, and employee management"


class LegalAction(Action):
    """Legal-related action for business agents."""
    
    name: str = "LegalAction"
    
    def __init__(self, **kwargs):
        """Initialize LegalAction."""
        super().__init__(**kwargs)
        self.desc = "Manage legal compliance, contracts, and regulatory matters"


class ITAction(Action):
    """Information Technology action for business agents."""
    
    name: str = "ITAction"
    
    def __init__(self, **kwargs):
        """Initialize ITAction."""
        super().__init__(**kwargs)
        self.desc = "Handle IT infrastructure, software development, and technical support"


class ProductAction(Action):
    """Product management action for business agents."""
    
    name: str = "ProductAction"
    
    def __init__(self, **kwargs):
        """Initialize ProductAction."""
        super().__init__(**kwargs)
        self.desc = "Manage product development, roadmaps, and lifecycle"


class ResearchAction(Action):
    """Research and Development action for business agents."""
    
    name: str = "ResearchAction"
    
    def __init__(self, **kwargs):
        """Initialize ResearchAction."""
        super().__init__(**kwargs)
        self.desc = "Conduct research, analysis, and innovation activities"
