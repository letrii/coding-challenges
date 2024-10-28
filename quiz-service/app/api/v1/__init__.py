from app.api.v1 import quiz
from fastapi import APIRouter

router = APIRouter()

router.include_router(quiz.router, prefix="/quizzes", tags=["quizzes"])
