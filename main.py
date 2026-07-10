import os
from typing import Dict, Any, List
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage
from langgraph.graph import StateGraph, END
from pydantic import BaseModel, Field

# ==========================================
# 1. ENTERPRISE DATA GOVERNANCE LAYER (Unity Catalog)
# ==========================================
class UnityCatalogGuardrail:
    """
    Simulates Databricks Unity Catalog role-based access control (RBAC) 
    and data lineage compliance checks.
    """
    def __init__(self, user_role: str):
        self.user_role = user_role
        # Define secure tables cataloged under Unity Catalog
        self.governed_catalog = {
            "catalog.retail_expansion.macro_metrics": ["Data Scientist", "Strategic Analyst"],
            "catalog.retail_expansion.alpha_sentiment": ["Strategic Analyst"]
        }

    def validate_access(self, asset_name: str) -> bool:
        required_roles = self.governed_catalog.get(asset_name, [])
        if self.user_role in required_roles:
            print(f"🔒 [Unity Catalog]: Access GRANTED to '{asset_name}' for role '{self.user_role}'.")
            return True
        print(f"❌ [Unity Catalog]: Access DENIED to '{asset_name}' for role '{self.user_role}'.")
        return False


# ==========================================
# 2. MODEL CONTEXT PROTOCOL (MCP) TOOLS
# ==========================================
class DatabricksVectorSearchTool(BaseModel):
    """Simulates secure semantic search retrieval over structured catalogs."""
    query: str = Field(description="The natural language query targeting macro-risk factors.")
    target_catalog: str = Field(description="The precise Unity Catalog path to query.")

    def run(self, guardrail: UnityCatalogGuardrail) -> str:
        if not guardrail.validate_access(self.target_catalog):
            return "Security Exception: Insufficient privileges under Unity Catalog rules."
        
        # Simulating vector search retrieval matches
        print(f"🔍 [MCP Tool]: Executing Vector Search for: '{self.query}'...")
        if "fragmentation" in self.query.lower():
            return "Match found: Macroeconomic report indicates a 'two-speed expansion'. Stable wealth markets show structural health (Life Expectancy > 73.15) but growth stagnation."
        return "Match found: Base indicators stable."


# ==========================================
# 3. LANGGRAPH ORCHESTRATION PIPELINE
# ==========================================
class AgentState(BaseModel):
    messages: List[Dict[str, Any]] = []
    user_role: str
    authorized: bool = False

def security_node(state: AgentState) -> Dict[str, Any]:
    """Node 1: Evaluates user privileges before tool invocation."""
    guardrail = UnityCatalogGuardrail(user_role=state.user_role)
    # Validate base infrastructure access
    is_authorized = guardrail.validate_access("catalog.retail_expansion.macro_metrics")
    return {"authorized": is_authorized}

def agent_logic_node(state: AgentState) -> Dict[str, Any]:
    """Node 2: Simulates LLM processing user intent and invoking the MCP tool."""
    if not state.authorized:
        return {"messages": state.messages + [{"role": "assistant", "content": "Routing blocked due to governance constraints."}]}
    
    last_user_message = next(msg["content"] for msg in reversed(state.messages) if msg["role"] == "user")
    
    # Initialize tool using Model Context Protocol structural mapping
    mcp_tool = DatabricksVectorSearchTool(
        query=last_user_message, 
        target_catalog="catalog.retail_expansion.macro_metrics"
    )
    
    guardrail = UnityCatalogGuardrail(user_role=state.user_role)
    tool_output = mcp_tool.run(guardrail)
    
    response = f"Agent Output combined with MCP data context:\n{tool_output}"
    return {"messages": state.messages + [{"role": "assistant", "content": response}]}

# Build the Graph Workflow
workflow = StateGraph(AgentState)
workflow.add_node("VerifyGovernance", security_node)
workflow.add_node("ExecuteAgentAI", agent_logic_node)

workflow.set_entry_point("VerifyGovernance")
workflow.add_edge("VerifyGovernance", "ExecuteAgentAI")
workflow.add_edge("ExecuteAgentAI", END)

app = workflow.compile()


# ==========================================
# 4. EXECUTION DEMO FOR RECRUITERS
# ==========================================
if __name__ == "__main__":
    print("--- Test Run 1: Authorized Strategic Analyst User ---")
    initial_state_analyst = {
        "messages": [{"role": "user", "content": "Check market data for trade fragmentation parameters."}],
        "user_role": "Strategic Analyst"
    }
    output_analyst = app.invoke(initial_state_analyst)
    print(f"Final Agent Prompt Summary: {output_analyst['messages'][-1]['content']}\n")

    print("--- Test Run 2: Unauthorized Guest User ---")
    initial_state_guest = {
        "messages": [{"role": "user", "content": "Access restricted market expansion pipelines."}],
        "user_role": "Guest User"
    }
    output_guest = app.invoke(initial_state_guest)
    print(f"Final Agent Prompt Summary: {output_guest['messages'][-1]['content']}")
