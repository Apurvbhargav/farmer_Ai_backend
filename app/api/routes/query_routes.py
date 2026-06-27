from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from langgraph.types import Command
import logging

from app.api.schemas.conversation_schema import (
    StartConversationRequest,
    FollowupAnswerRequest
)

from app.core.security.auth_guard import get_current_farmer
from app.db.session import SessionLocal
from app.services.conversation_service import (
    create_conversation,
    get_conversation,
    add_followup_answer,
    update_conversation,
    complete_conversation
)
from app.graph.workflow import create_farmer_graph

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/conversation",
    tags=["Conversation"]
)

graph = create_farmer_graph()


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


@router.post("/start")
def start_conversation(
    request: StartConversationRequest,
    farmer_id: int = Depends(get_current_farmer),
    db: Session = Depends(get_db)
):
    convo = create_conversation(
        db,
        farmer_id,
        request.query
    )

    initial_state = {
        "farmer_id": farmer_id,
        "query": request.query,
        "conversation_id": convo.id,
        "analysis": None,
        "retrieved_memories": None,
        "followup_questions": [],
        "needs_followup": False,
        "followup_answers": {},
        "recommendation": None,
        "confidence": 0.0,
        "missing_fields": [],
        "current_question_index": 0
    }

    config = {
        "configurable": {
            "thread_id": str(convo.id)
        }
    }

    try:
        output = graph.invoke(
            initial_state,
            config=config
        )

    except Exception as e:
        logger.error(f"Graph error: {e}")
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

    interrupts = output.get("__interrupt__")

    if interrupts:
        interrupt_data = interrupts[0].value

        update_conversation(db, convo.id, {
            "analysis": output.get("analysis"),
            "retrieved_memories": output.get("retrieved_memories"),
            "current_question": interrupt_data.get("question")
        })

        return {
            "conversation_id": convo.id,
            "status": "waiting_for_followup",
            "question": interrupt_data.get("question"),
            "question_number": interrupt_data.get("question_number"),
            "total_questions": interrupt_data.get("total_questions")
        }

    update_conversation(db, convo.id, {
        "analysis": output.get("analysis"),
        "retrieved_memories": output.get("retrieved_memories"),
        "current_question": None
    })

    if output.get("recommendation"):
        complete_conversation(
            db,
            convo.id
        )

        return {
            "conversation_id": convo.id,
            "status": "completed",
            "recommendation": output["recommendation"]
        }

    raise HTTPException(
        status_code=500,
        detail="Unexpected workflow state"
    )


@router.post("/followup")
def followup_conversation(
    request: FollowupAnswerRequest,
    farmer_id: int = Depends(get_current_farmer),
    db: Session = Depends(get_db)
):
    convo = get_conversation(
        db,
        request.conversation_id
    )

    if not convo or convo.farmer_id != farmer_id:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found"
        )

    answer_key = f"answer_{len(convo.followup_answers or {})}"

    add_followup_answer(
        db,
        request.conversation_id,
        answer_key,
        request.answer
    )

    config = {
        "configurable": {
            "thread_id": str(request.conversation_id)
        }
    }

    try:
        output = graph.invoke(
            Command(resume=request.answer),
            config=config
        )

    except Exception as e:
        logger.error(f"Followup error: {e}")
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

    interrupts = output.get("__interrupt__")

    if interrupts:
        interrupt_data = interrupts[0].value

        update_conversation(db, request.conversation_id, {
            "analysis": output.get("analysis"),
            "retrieved_memories": output.get("retrieved_memories"),
            "current_question": interrupt_data.get("question")
        })

        return {
            "conversation_id": request.conversation_id,
            "status": "waiting_for_followup",
            "question": interrupt_data.get("question"),
            "question_number": interrupt_data.get("question_number"),
            "total_questions": interrupt_data.get("total_questions")
        }

    update_conversation(db, request.conversation_id, {
        "analysis": output.get("analysis"),
        "retrieved_memories": output.get("retrieved_memories"),
        "current_question": None
    })

    if output.get("recommendation"):
        complete_conversation(
            db,
            request.conversation_id
        )

        return {
            "conversation_id": request.conversation_id,
            "status": "completed",
            "recommendation": output["recommendation"]
        }

    raise HTTPException(
        status_code=500,
        detail="Unexpected workflow state"
    )