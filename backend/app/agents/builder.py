from typing import Any
from langchain_core.messages import AIMessage, BaseMessage
from langchain_openai import AzureChatOpenAI
from langgraph.graph import END, StateGraph
from langgraph.prebuilt import ToolNode
from pydantic import BaseModel, Field

from app.core.config import get_settings

settings = get_settings()

class AgentState(BaseModel):
    """Represents the state of the agent loop."""
    messages: list[BaseMessage] = Field(default_factory=list)
    tasks: list[str] = Field(default_factory=list)
    current_task: str | None = None
    workspace_files: list[str] = Field(default_factory=list)

def create_agent_executor(tools: list[Any], system_prompt: str, llm: Any = None):
    """
    Builds the LangGraph state machine for the DeepAgent.
    Included logic: Planning -> Tool Execution -> Final Response.
    """
    if llm is None:
        llm = AzureChatOpenAI(
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
            api_key=settings.AZURE_OPENAI_API_KEY, # type: ignore
            api_version="2024-02-15-preview",
            azure_deployment=settings.AZURE_OPENAI_NORMAL_DEPLOYMENT,
            temperature=0.7,
        )

    # Pre-bind tools to the LLM
    llm_with_tools = llm.bind_tools(tools)

    workflow = StateGraph(AgentState)

    # Define the core reasoning node
    def call_model(state: AgentState):
        prompt = [AIMessage(content=system_prompt)]
        messages = prompt + state.messages
        response = llm_with_tools.invoke(messages)
        return {"messages": [response]}

    # Define tool execution node using ToolNode
    tool_node = ToolNode(tools)

    def should_continue(state: AgentState):
        last_message = state.messages[-1]
        if isinstance(last_message, AIMessage) and last_message.tool_calls:
            return "continue"
        return "end"

    # Add nodes to graph
    workflow.add_node("agent", call_model)
    workflow.add_node("action", tool_node)

    workflow.set_entry_point("agent")
    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {
            "continue": "action",
            "end": END
        }
    )
    workflow.add_edge("action", "agent")

    return workflow.compile()
