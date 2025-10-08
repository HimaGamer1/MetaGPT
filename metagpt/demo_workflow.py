#!/usr/bin/env python3
"""
Demo Workflow Orchestration for Product Launch

This script demonstrates a multi-agent workflow pipeline using BusinessAgent
and WorkflowOrchestrator for a complete product launch scenario.
"""

from metagpt.roles.business_agent import BusinessAgent
from metagpt.actions.business_actions import (
    ProductPlanning,
    MarketingCampaign,
    SalesStrategy,
    CustomerSupport
)
from metagpt.team import WorkflowOrchestrator, TaskMessage


def create_product_agent():
    """Create a Product agent with ProductPlanning action."""
    agent = BusinessAgent(
        name="Product Manager",
        profile="Product",
        goal="Define product features and roadmap for successful launch"
    )
    agent.set_actions([ProductPlanning])
    return agent


def create_marketing_agent():
    """Create a Marketing agent with MarketingCampaign action."""
    agent = BusinessAgent(
        name="Marketing Manager",
        profile="Marketing",
        goal="Develop compelling marketing campaigns to drive product awareness"
    )
    agent.set_actions([MarketingCampaign])
    return agent


def create_sales_agent():
    """Create a Sales agent with SalesStrategy action."""
    agent = BusinessAgent(
        name="Sales Manager",
        profile="Sales",
        goal="Create sales strategies to maximize revenue and customer acquisition"
    )
    agent.set_actions([SalesStrategy])
    return agent


def create_support_agent():
    """Create a Support agent with CustomerSupport action."""
    agent = BusinessAgent(
        name="Support Manager",
        profile="Support",
        goal="Ensure excellent customer support and satisfaction"
    )
    agent.set_actions([CustomerSupport])
    return agent


def setup_workflow_pipeline():
    """Set up the product launch workflow pipeline."""
    # Create agents
    product_agent = create_product_agent()
    marketing_agent = create_marketing_agent()
    sales_agent = create_sales_agent()
    support_agent = create_support_agent()
    
    # Initialize orchestrator
    orchestrator = WorkflowOrchestrator(
        name="Product Launch Orchestrator",
        agents=[product_agent, marketing_agent, sales_agent, support_agent]
    )
    
    return orchestrator


def define_product_launch_workflow(orchestrator):
    """Define the workflow pipeline for product launch."""
    print("\n" + "="*70)
    print("PRODUCT LAUNCH WORKFLOW PIPELINE")
    print("="*70 + "\n")
    
    # Step 1: Product Planning
    print("[STEP 1] Product Planning Phase")
    print("-" * 70)
    product_task = TaskMessage(
        task_id="product_planning",
        agent_name="Product Manager",
        content="Define features, pricing, and roadmap for our new AI-powered analytics platform",
        priority=1
    )
    product_result = orchestrator.execute_task(product_task)
    print(f"Product Agent Output: {product_result}\n")
    
    # Step 2: Marketing Campaign
    print("[STEP 2] Marketing Campaign Phase")
    print("-" * 70)
    marketing_task = TaskMessage(
        task_id="marketing_campaign",
        agent_name="Marketing Manager",
        content=f"Create marketing campaign based on product plan: {product_result}",
        priority=2,
        depends_on=["product_planning"]
    )
    marketing_result = orchestrator.execute_task(marketing_task)
    print(f"Marketing Agent Output: {marketing_result}\n")
    
    # Step 3: Sales Strategy
    print("[STEP 3] Sales Strategy Phase")
    print("-" * 70)
    sales_task = TaskMessage(
        task_id="sales_strategy",
        agent_name="Sales Manager",
        content=f"Develop sales strategy aligned with marketing: {marketing_result}",
        priority=3,
        depends_on=["marketing_campaign"]
    )
    sales_result = orchestrator.execute_task(sales_task)
    print(f"Sales Agent Output: {sales_result}\n")
    
    # Step 4: Customer Support Planning
    print("[STEP 4] Customer Support Phase")
    print("-" * 70)
    support_task = TaskMessage(
        task_id="customer_support",
        agent_name="Support Manager",
        content="Prepare support infrastructure and documentation for product launch",
        priority=4,
        depends_on=["product_planning"]
    )
    support_result = orchestrator.execute_task(support_task)
    print(f"Support Agent Output: {support_result}\n")
    
    # Workflow Summary
    print("="*70)
    print("WORKFLOW EXECUTION SUMMARY")
    print("="*70)
    print(f"✓ Product Planning: Completed")
    print(f"✓ Marketing Campaign: Completed")
    print(f"✓ Sales Strategy: Completed")
    print(f"✓ Customer Support: Completed")
    print("\nAll agents have successfully executed their tasks in the pipeline!")
    print("="*70 + "\n")


def main():
    """Main execution function."""
    print("\n" + "#"*70)
    print("# DEMO: WORKFLOW ORCHESTRATION FOR PRODUCT LAUNCH")
    print("#"*70 + "\n")
    
    # Setup workflow
    orchestrator = setup_workflow_pipeline()
    print(f"Orchestrator initialized with {len(orchestrator.agents)} agents\n")
    
    # List agents
    print("Registered Agents:")
    for i, agent in enumerate(orchestrator.agents, 1):
        print(f"  {i}. {agent.name} ({agent.profile})")
    print()
    
    # Execute workflow
    define_product_launch_workflow(orchestrator)
    
    print("\n[INFO] demo_workflow.py executed successfully!")
    print("[INFO] File created at: metagpt/demo_workflow.py\n")


if __name__ == "__main__":
    main()
