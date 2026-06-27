"""
LangGraph Workflow for Farmer AI Backend
This file contains the complete graph structure for the multi-turn farmer conversation system.
"""

from typing import TypedDict, Optional, List, Dict, Any

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import interrupt
from langgraph.types import Command
from app.agents.context_agent import analyze_farmer_query
from app.agents.followup_agent import generate_followup_questions
from app.agents.recommendation_agent import generate_recommendation
from app.db.session import SessionLocal
from app.services.memory_service import save_memory_event


# ============================================================================
# STATE DEFINITION
# ============================================================================

class FarmerConversationState(TypedDict):
    """State object that flows through the entire graph"""

    # Input
    farmer_id: int
    query: str
    conversation_id: int

    # Analysis results
    analysis: Optional[Dict[str, Any]]

    # Retrieved memories
    retrieved_memories: Optional[List[Dict[str, Any]]]

    # Followup questions and answers
    followup_questions: Optional[List[str]]
    needs_followup: bool
    followup_answers: Dict[str, str]

    # Final recommendation
    recommendation: Optional[Dict[str, Any]]

    # Metadata
    confidence: float
    missing_fields: List[str]
    current_question_index: int


# ============================================================================
# NODE DEFINITIONS
# ============================================================================

def context_node(state: FarmerConversationState) -> FarmerConversationState:
    """
    NODE 1: CONTEXT ANALYSIS
    Analyzes farmer's query and extracts structured agricultural intelligence
    """
    print("\n" + "=" * 60)
    print("CONTEXT NODE: Analyzing farmer query...")
    print("=" * 60)

    db = SessionLocal()

    try:
        result = analyze_farmer_query(
            query=state["query"],
            farmer_id=state["farmer_id"],
            db=db
        )
    finally:
        db.close()

    analysis = result.get("analysis", {})
    retrieved_memories = result.get("retrieved_memories", [])

    state["analysis"] = analysis
    state["confidence"] = analysis.get("confidence", 0)
    state["missing_fields"] = analysis.get("missing_fields", [])
    state["retrieved_memories"] = retrieved_memories

    print("Analysis Complete:")
    print(f"  - Event Type: {analysis.get('event_type')}")
    print(f"  - Crop: {analysis.get('crop')}")
    print(f"  - Confidence: {state['confidence']}")
    print(f"  - Missing Fields: {state['missing_fields']}")
    print(f"  - Memories Retrieved: {len(state['retrieved_memories'])}")

    return state


def followup_node(state: FarmerConversationState) -> FarmerConversationState:
    """
    NODE 2: FOLLOWUP DECISION
    Determines if more information is needed from the farmer
    """
    print("\n" + "=" * 60)
    print("FOLLOWUP NODE: Checking if more info needed...")
    print("=" * 60)

    followup = generate_followup_questions(
        analysis=state["analysis"]
    )

    state["needs_followup"] = followup.get("needs_followup", False)
    state["followup_questions"] = followup.get("followup_questions", [])

    print("Followup Decision:")
    print(f"  - Needs Followup: {state['needs_followup']}")
    print(f"  - Reason: {followup.get('reason')}")

    if state["needs_followup"]:
        print(f"  - Questions to Ask: {len(state['followup_questions'])}")

        for index, question in enumerate(state["followup_questions"][:3], 1):
            print(f"    {index}. {question}")

    return state


def ask_question_node(state: FarmerConversationState) -> FarmerConversationState:
    """
    NODE 3: HUMAN INPUT
    Pauses graph execution and waits for user answer.
    """

    print("\n" + "=" * 60)
    print("ASK QUESTION NODE")
    print("=" * 60)

    current_index = state["current_question_index"]

    question = state["followup_questions"][current_index]

    print(f"Current Question: {question}")

    answer = interrupt(
        {
            "question": question,
            "question_number": current_index + 1,
            "total_questions": len(state["followup_questions"])
        }
    )

    state["followup_answers"][
        f"answer_{current_index}"
    ] = answer

    state["current_question_index"] += 1

    return state


def recommendation_node(state: FarmerConversationState) -> FarmerConversationState:
    """
    NODE 4: GENERATE RECOMMENDATION
    Creates personalized agricultural recommendation based on analysis and history.
    """
    print("\n" + "=" * 60)
    print("RECOMMENDATION NODE: Generating recommendation...")
    print("=" * 60)

    recommendation = generate_recommendation(
        analysis=state["analysis"],
        memories=state["retrieved_memories"],
        followup_answers=state["followup_answers"]
    )

    state["recommendation"] = recommendation

    print("Recommendation Generated:")
    print(f"  - Problem: {recommendation.get('problem_summary')}")
    print(f"  - Priority: {recommendation.get('priority')}")
    print(f"  - Needs Expert: {recommendation.get('needs_expert')}")

    if state["analysis"]:
        db = SessionLocal()

        try:
            save_memory_event(
                db=db,
                farmer_id=state["farmer_id"],
                event_type=state["analysis"].get("event_type"),
                crop_name=state["analysis"].get("crop"),
                details=state["analysis"],
                source_query=state["query"],
                confidence=state["confidence"]
            )

            print("Memory Event Saved")
        finally:
            db.close()

    return state


# ============================================================================
# CONDITIONAL ROUTING FUNCTIONS
# ============================================================================

def route_after_followup(state: FarmerConversationState) -> str:
    """
    After followup generation.
    """

    if state["needs_followup"] and state["followup_questions"]:
        return "ask_question"

    return "recommendation"


def route_after_question(state: FarmerConversationState) -> str:
    """
    After each answered question.
    """

    if state["current_question_index"] < len(state["followup_questions"]):
        return "ask_question"

    return "recommendation"


# ============================================================================
# GRAPH CONSTRUCTION
# ============================================================================

def create_farmer_graph():
    """
    Constructs and returns the complete LangGraph workflow.
    """

    workflow = StateGraph(FarmerConversationState)

    workflow.add_node("context", context_node)
    workflow.add_node("followup", followup_node)
    workflow.add_node("ask_question", ask_question_node)
    workflow.add_node("recommendation", recommendation_node)

    workflow.set_entry_point("context")

    workflow.add_edge("context", "followup")

    workflow.add_conditional_edges(
        "followup",
        route_after_followup,
        {
            "ask_question": "ask_question",
            "recommendation": "recommendation"
        }
    )

    workflow.add_conditional_edges(
        "ask_question",
        route_after_question,
        {
            "ask_question": "ask_question",
            "recommendation": "recommendation"
        }
    )

    workflow.add_edge("recommendation", END)

    memory = MemorySaver()

    graph = workflow.compile(
        checkpointer=memory
    )

    return graph