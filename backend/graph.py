import sqlite3
from typing import TypedDict, List

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.sqlite import SqliteSaver

from agents import (
    ingestion_agent,
    classification_agent,
    confidence_router,
    drafting_agent,
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

    graph.add_node("ingestion", ingestion_agent)
    graph.add_node("classification", classification_agent)
    graph.add_node("confidence", confidence_router)
    graph.add_node("drafting", drafting_agent)
    graph.add_node("reject", reject_agent)

    graph.add_edge(START, "ingestion")
    graph.add_edge("ingestion", "classification")
    graph.add_edge("classification", "confidence")

    graph.add_conditional_edges(
        "confidence",
        lambda state: state["route"],
        {
            "auto_approved": "drafting",
            "approved": "drafting",
            "rejected": "reject",
        },
    )

    graph.add_edge("drafting", END)
    graph.add_edge("reject", END)

    conn = sqlite3.connect("checkpoints.sqlite", check_same_thread=False)
    checkpointer = SqliteSaver(conn)
    return graph.compile(checkpointer=checkpointer)


pipeline = build_graph()