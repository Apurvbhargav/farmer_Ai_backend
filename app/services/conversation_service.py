from sqlalchemy.orm import Session

from app.db.models.conversation_model import FarmerConversation


def create_conversation(db: Session, farmer_id: int, query: str):

    convo = FarmerConversation(
        farmer_id=farmer_id,
        original_query=query,
        status="active",
        followup_answers={}
    )

    db.add(convo)
    db.commit()
    db.refresh(convo)

    return convo


def get_conversation(db: Session, conversation_id: int):

    return db.query(FarmerConversation).filter(
        FarmerConversation.id == conversation_id
    ).first()


def update_conversation(db: Session, conversation_id: int, updates: dict):

    convo = get_conversation(db, conversation_id)

    if not convo:
        return None

    for key, value in updates.items():
        setattr(convo, key, value)

    db.commit()
    db.refresh(convo)

    return convo


def add_followup_answer(db: Session, conversation_id: int, key: str, value: str):

    convo = get_conversation(db, conversation_id)

    if not convo:
        return None

    answers = convo.followup_answers or {}
    answers[key] = value

    convo.followup_answers = answers

    db.commit()
    db.refresh(convo)

    return convo


def complete_conversation(db: Session, conversation_id: int):

    convo = get_conversation(db, conversation_id)

    if convo:
        convo.status = "completed"
        db.commit()
        db.refresh(convo)

    return convo