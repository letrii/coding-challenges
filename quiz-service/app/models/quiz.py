from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class QuestionType(str, Enum):
    MULTIPLE_CHOICE = "multiple_choice"
    TRUE_FALSE = "true_false"


class Question(BaseModel):
    id: str = Field(..., description="Question ID")
    text: str
    type: QuestionType
    options: List[str]
    correct_answer: str
    points: int = 1
    time_limit: int = 30  # seconds


class Quiz(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    title: str
    description: str
    questions: List[Question]
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class QuizSession(BaseModel):
    id: str
    quiz_id: str
    status: str = "waiting"  # "waiting", "active", "completed"
    current_question: int = 0
    questions: List[Question]
    start_time: datetime
    end_time: Optional[datetime] = None
    participants: List[str] = []
    updated_at: Optional[datetime] = None

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class Answer(BaseModel):
    session_id: str
    question_id: str
    user_id: str
    answer: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
