from typing import TypedDict, List

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from agents import (
    ingestion_agent,
    classification_agent,
    confidence_router,
    human_review_agent,
    reject_agent,
)


class SlipState(TypedDict):
    new_files: List[dict]
    extracted: List[dict]
    classified: List[dict]
    routed: List[dict]
    route: str
    current_slip: dict  


def build_graph():
    graph = StateGraph(SlipState)

    # Nodes
    graph.add_node("ingestion", ingestion_agent)
    graph.add_node("classification", classification_agent)
    graph.add_node("confidence", confidence_router)
    graph.add_node("human_review", human_review_agent)
    graph.add_node("reject", reject_agent)

    # Main pipeline
    graph.add_edge(START, "ingestion")
    graph.add_edge("ingestion", "classification")
    graph.add_edge("classification", "confidence")

    # Route based on confidence decision
    graph.add_conditional_edges(
        "confidence",
        lambda state: state["route"],
        {
            "auto_approved": END,
            "needs_human_review": "human_review",
            "rejected": "reject",
        },
    )

    # Placeholder nodes
    graph.add_edge("human_review", END)
    graph.add_edge("reject", END)

    # Save paused state for interrupts
    checkpointer = MemorySaver()
    return graph.compile(checkpointer=checkpointer)


pipeline = build_graph()