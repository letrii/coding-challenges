import logging
import asyncio


from app.services.quiz_service import QuizService
from app.models.quiz import Quiz, Answer, QuizSession
from app.websockets.manager import manager
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    WebSocket,
    WebSocketDisconnect,
    status,
    Query,
)
from typing import Dict, List, Optional

router = APIRouter()
quiz_service = QuizService()
logger = logging.getLogger(__name__)


@router.on_event("startup")
async def startup_event():
    await quiz_service.setup()


@router.on_event("shutdown")
async def shutdown_event():
    await quiz_service.cleanup()


@router.post("/quizzes/", response_model=Quiz, status_code=201)
async def create_quiz(quiz: Quiz) -> Quiz:
    """Create a new quiz"""
    return await quiz_service.create_quiz(quiz)


@router.post("/quizzes/sessions", response_model=QuizSession)
async def create_quiz_session(
    quiz_id: str = Query(..., description="ID of the quiz to create a session for")
):
    """Create a new quiz session"""
    logger.info(f"Creating new session for quiz: {quiz_id}")
    return await quiz_service.create_session(quiz_id)


@router.get("/quizzes/sessions/{session_id}", response_model=Optional[QuizSession])
async def get_session(session_id: str) -> Optional[QuizSession]:
    """Get session details"""
    session = await quiz_service.get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.post("/quizzes/sessions/{session_id}/start")
async def start_quiz_session(session_id: str):
    """Start a quiz session"""
    try:
        session = await quiz_service.start_session(session_id)
        return {
            "status": "success",
            "message": "Session started successfully",
            "session": session.model_dump(),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting session: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to start session: {str(e)}"
        )


@router.post("/quizzes/sessions/{session_id}/submit")
async def submit_quiz_answer(session_id: str, answer: Answer):
    """Submit answer for current question"""
    if session_id != answer.session_id:
        raise HTTPException(status_code=400, detail="Session ID mismatch")
    return await quiz_service.submit_answer(answer)


@router.get("/quizzes/sessions/{session_id}/leaderboard")
async def get_quiz_leaderboard(session_id: str, limit: int = 10):
    """Get session leaderboard"""
    return await quiz_service.get_leaderboard(session_id, limit)


@router.websocket("/quizzes/sessions/{session_id}/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str, user_id: str):
    """WebSocket endpoint for real-time quiz updates"""
    logger.info(
        f"New WebSocket connection request: session={session_id}, user={user_id}"
    )

    try:
        await websocket.accept()
        logger.info(f"WebSocket connection accepted for user {user_id}")

        await manager.connect(websocket, session_id, user_id)

        try:
            session = await quiz_service.get_session(session_id)
            if not session:
                logger.error(f"Session not found: {session_id}")
                await websocket.send_json(
                    {"type": "error", "error": "Session not found"}
                )
                return

            await websocket.send_json(
                {
                    "type": "session_state",
                    "session_id": session_id,
                    "status": session.status,
                    "current_question": session.current_question,
                    "total_questions": (
                        len(session.questions) if session.questions else 0
                    ),
                    "questions": [q.model_dump() for q in session.questions],
                    "participants": session.participants,
                }
            )

            session = await quiz_service.add_participant(
                session_id, user_id, notify=True
            )

            while True:
                try:
                    data = await websocket.receive_json()
                    logger.debug(f"Received message from user {user_id}: {data}")

                    if data.get("type") == "ping":
                        await websocket.send_json({"type": "pong"})
                        continue

                except WebSocketDisconnect:
                    logger.info(f"WebSocket disconnected for user {user_id}")
                    break
                except Exception as e:
                    logger.error(f"Error processing message: {e}")
                    break

        finally:
            user_fully_disconnected = await manager.disconnect(
                websocket, session_id, user_id
            )

            if user_fully_disconnected:
                try:
                    await quiz_service.remove_participant(
                        session_id, user_id, notify=True
                    )
                    logger.info(
                        f"User {user_id} fully disconnected from session {session_id}"
                    )
                except Exception as e:
                    logger.error(f"Error handling participant departure: {e}")
            else:
                logger.info(
                    f"User {user_id} still has other connections to session {session_id}"
                )

    except Exception as e:
        logger.error(f"WebSocket error for user {user_id}: {e}")
