from fastapi import (
    APIRouter,
    Depends
)

from sqlalchemy.orm import Session

from app.api.schemas.query_schema import (
    QueryRequest
)

from app.agents.context_agent import (
    analyze_farmer_query
)

from app.agents.followup_agent import (
    generate_followup_questions
)

from app.agents.recommendation_agent import (
    generate_recommendation
)

from app.services.memory_service import (
    save_memory_event
)

from app.core.security.auth_guard import (
    get_current_farmer
)

from app.db.session import SessionLocal


router = APIRouter(
    prefix="/query",
    tags=["Query"]
)


def get_db():

    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()


@router.post("/analyze")
def analyze_query(
    request: QueryRequest,
    farmer_id: int = Depends(get_current_farmer),
    db: Session = Depends(get_db)
):

    # STEP 1
    # Context Agent + Memory Retrieval

    context_result = analyze_farmer_query(
        db=db,
        farmer_id=farmer_id,
        query=request.query
    )

    analysis = context_result[
        "analysis"
    ]

    retrieved_memories = context_result[
        "retrieved_memories"
    ]

    # STEP 2
    # Followup Agent

    followup = generate_followup_questions(
        analysis=analysis
    )

    # STEP 3
    # Recommendation Agent

    recommendation = generate_recommendation(

        analysis=analysis,

        memories=retrieved_memories,

        followup_answers={}
    )

    # STEP 4
    # Save Memory

    if analysis.get("should_store_memory"):

        save_memory_event(

            db=db,

            farmer_id=farmer_id,

            event_type=analysis.get(
                "event_type"
            ),

            crop_name=analysis.get(
                "crop"
            ),

            details={

                "action":
                    analysis.get(
                        "action"
                    ),

                "chemical":
                    analysis.get(
                        "chemical"
                    ),

                "days_ago":
                    analysis.get(
                        "days_ago"
                    )
            },

            source_query=request.query,

            confidence=int(
                analysis.get(
                    "confidence",
                    0
                ) * 100
            )
        )

    # FINAL RESPONSE

    return {

        "farmer_id": farmer_id,

        "analysis": analysis,

        "followup": followup,

        "recommendation": recommendation
    }