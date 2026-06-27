from pydantic import BaseModel
from typing import Optional


class StartConversationRequest(BaseModel):
    query: str


class FollowupAnswerRequest(BaseModel):
    conversation_id: int
    answer: str