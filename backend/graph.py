from langgraph.graph import StateGraph, START, END
from typing import TypedDict, List
from agents import ingestion_agent, classification_agent, confidence_router

class SlipState(TypedDict):
    new_files: List[dict]
    extracted: List[dict]
    classified: List[dict]
    routed: List[dict]

def build_graph():
    graph = StateGraph(SlipState)

    graph.add_node("ingestion", ingestion_agent)
    graph.add_node("classification", classification_agent)
    graph.add_node("confidence", confidence_router)

    graph.add_edge(START, "ingestion")
    graph.add_edge("ingestion", "classification")
    graph.add_edge("classification", "confidence")
    graph.add_edge("confidence", END)

    return graph.compile()

pipeline = build_graph()
