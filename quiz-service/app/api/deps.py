from app.services.quiz_service import QuizService


async def get_quiz_service():
    service = QuizService()
    await service.setup()
    yield service
