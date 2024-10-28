import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional

from app.core.config import get_settings
from app.models.quiz import Answer, Quiz, QuizSession
from app.websockets.manager import manager
from bson import ObjectId
from fastapi import HTTPException, WebSocket
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from redis.asyncio import Redis

logger = logging.getLogger(__name__)


class QuizService:
    def __init__(self):
        self.settings = get_settings()
        self.redis: Redis = None
        self.mongodb: AsyncIOMotorClient = None
        self.db: AsyncIOMotorDatabase = None

    async def setup(self):
        try:
            retries = 5
            while retries > 0:
                try:
                    self.redis = Redis.from_url(
                        self.settings.REDIS_URL,
                        decode_responses=True,
                        retry_on_timeout=True,
                    )
                    await self.redis.ping()

                    logger.info(
                        f"Connecting to MongoDB at: {self.settings.MONGODB_URL}"
                    )
                    self.mongodb = AsyncIOMotorClient(
                        self.settings.MONGODB_URL,
                        serverSelectionTimeoutMS=5000,
                        connectTimeoutMS=5000,
                        retryWrites=True,
                        retryReads=True,
                    )

                    await self.mongodb.admin.command("ping")
                    self.db = self.mongodb[self.settings.MONGODB_DB]
                    await self.setup_collections()

                    logger.info("Successfully connected to MongoDB and Redis")
                    break

                except Exception as e:
                    retries -= 1
                    if retries == 0:
                        logger.error(f"Failed to connect after all retries: {str(e)}")
                        raise
                    logger.warning(
                        f"Failed to connect to databases, retrying... ({retries} attempts left)"
                    )
                    await asyncio.sleep(5)

        except Exception as e:
            logger.error(f"Failed to setup database connections: {str(e)}")
            raise

    async def cleanup(self):
        """Cleanup database connections"""
        try:
            if self.redis is not None:
                await self.redis.close()
            if self.mongodb is not None:
                self.mongodb.close()
            logger.info("Database connections closed")
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")

    async def setup_collections(self):
        """Ensure all required collections exist"""
        try:
            collections = await self.db.list_collection_names()
            required_collections = ["quizzes", "sessions", "answers"]

            for collection in required_collections:
                if collection not in collections:
                    await self.db.create_collection(collection)
                    logger.info(f"Created collection: {collection}")

        except Exception as e:
            logger.error(f"Error setting up collections: {str(e)}")
            raise

    async def create_quiz(self, quiz: Quiz) -> Quiz:
        """Create a new quiz"""
        try:
            if self.db is None:
                raise HTTPException(
                    status_code=500, detail="Database connection not initialized"
                )

            quiz_dict = quiz.model_dump(exclude={"_id"} if quiz.id is None else set())
            quiz_dict["created_at"] = datetime.utcnow()
            quiz_dict["updated_at"] = datetime.utcnow()

            for question in quiz_dict["questions"]:
                if "id" not in question:
                    question["id"] = str(ObjectId())

            result = await self.db.quizzes.insert_one(quiz_dict)
            quiz.id = str(result.inserted_id)
            return quiz

        except Exception as e:
            logger.error(f"Error creating quiz: {str(e)}")
            raise HTTPException(
                status_code=500, detail=f"Failed to create quiz: {str(e)}"
            )

    async def get_quiz(self, quiz_id: str) -> Optional[Quiz]:
        """Get quiz details"""
        try:
            if self.db is None:
                raise HTTPException(
                    status_code=500, detail="Database connection not initialized"
                )

            try:
                obj_id = ObjectId(quiz_id)
            except:
                raise HTTPException(status_code=400, detail="Invalid quiz ID format")

            quiz_data = await self.db.quizzes.find_one({"_id": obj_id})
            if quiz_data is None:
                return None

            quiz_data["_id"] = str(quiz_data["_id"])
            return Quiz.model_validate(quiz_data)

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting quiz: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to get quiz: {str(e)}")

    async def create_session(self, quiz_id: str) -> QuizSession:
        """Create a new quiz session"""
        try:
            if self.db is None or self.redis is None:
                raise HTTPException(
                    status_code=500, detail="Database connections not initialized"
                )

            quiz = await self.get_quiz(quiz_id)
            if quiz is None:
                raise HTTPException(status_code=404, detail="Quiz not found")

            session = QuizSession(
                id=f"session_{quiz_id}_{int(datetime.utcnow().timestamp())}",
                quiz_id=quiz_id,
                start_time=datetime.utcnow(),
                status="waiting",
                current_question=0,
                questions=quiz.questions,
                participants=[],
            )

            await self.redis.setex(
                f"quiz_session:{session.id}",
                3600,  # 1 hour expiry
                session.model_dump_json(),
            )

            await self.db.sessions.insert_one(session.model_dump())

            logger.info(f"Created quiz session: {session.id}")
            return session

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error creating quiz session: {str(e)}")
            raise HTTPException(
                status_code=500, detail=f"Failed to create quiz session: {str(e)}"
            )

    async def get_leaderboard(self, session_id: str, limit: int = 10) -> List[Dict]:
        """Get session leaderboard"""
        try:
            if self.redis is None:
                raise HTTPException(
                    status_code=500, detail="Redis connection not initialized"
                )

            scores = await self.redis.zrevrange(
                f"leaderboard:{session_id}", 0, limit - 1, withscores=True
            )

            return [
                {"user_id": user_id, "score": int(score)} for user_id, score in scores
            ]

        except Exception as e:
            logger.error(f"Error getting leaderboard: {str(e)}")
            raise HTTPException(
                status_code=500, detail=f"Failed to get leaderboard: {str(e)}"
            )

    async def start_session(self, session_id: str):
        """Start a quiz session"""
        try:
            if self.db is None:
                raise HTTPException(
                    status_code=500, detail="Database connection not initialized"
                )

            session = await self.get_session(session_id)
            if not session:
                raise HTTPException(status_code=404, detail="Session not found")

            if session.status != "waiting":
                raise HTTPException(
                    status_code=400, detail="Session is not in waiting state"
                )

            if not session.questions:
                raise HTTPException(status_code=400, detail="Session has no questions")

            await self.db.sessions.update_one(
                {"id": session_id},
                {
                    "$set": {
                        "status": "active",
                        "current_question": 0,
                        "updated_at": datetime.utcnow(),
                    }
                },
            )

            session.status = "active"
            session.current_question = 0
            session_key = f"quiz_session:{session_id}"
            await self.redis.set(
                session_key, session.model_dump_json(), ex=3600  # 1 hour expiry
            )

            current_question = session.questions[0]

            await manager.broadcast_to_session(
                session_id,
                {
                    "type": "session_started",
                    "session_id": session_id,
                    "status": "active",
                    "current_question": current_question.model_dump(),
                    "question_number": 1,
                    "total_questions": len(session.questions),
                    "participants": session.participants,
                },
            )

            logger.info(
                f"Started session {session_id} with {len(session.participants)} participants"
            )
            return session

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error starting session: {str(e)}")
            raise HTTPException(
                status_code=500, detail=f"Failed to start session: {str(e)}"
            )

    async def submit_answer(self, answer: Answer) -> Dict:
        try:
            session_data = await self.redis.get(f"quiz_session:{answer.session_id}")
            if not session_data:
                raise HTTPException(status_code=404, detail="Session not found")

            session = QuizSession.model_validate_json(session_data)
            current_question = session.questions[session.current_question]

            is_correct = current_question.correct_answer == answer.answer
            points = current_question.points if is_correct else 0

            await self.db.answers.insert_one(
                {
                    **answer.model_dump(),
                    "is_correct": is_correct,
                    "points": points,
                    "timestamp": datetime.utcnow(),
                }
            )

            score_key = f"score:{answer.session_id}:{answer.user_id}"
            total_score = await self.redis.incrby(score_key, points)

            await self.redis.zadd(
                f"leaderboard:{answer.session_id}", {answer.user_id: total_score}
            )

            leaderboard = await self.get_leaderboard(answer.session_id)

            await manager.broadcast_to_session(
                answer.session_id,
                {
                    "type": "answer_submitted",
                    "user_id": answer.user_id,
                    "is_correct": is_correct,
                    "points": points,
                    "leaderboard": leaderboard,
                },
            )

            return {
                "status": "success",
                "is_correct": is_correct,
                "points": points,
                "total_score": total_score,
            }

        except Exception as e:
            logger.error(f"Error submitting answer: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to submit answer")

    async def add_participant(
        self, session_id: str, user_id: str, notify: bool = True
    ) -> QuizSession:
        """Add participant to session"""
        try:
            if self.db is None:
                raise HTTPException(
                    status_code=500, detail="Database connection not initialized"
                )

            session = await self.get_session(session_id)
            if not session:
                raise HTTPException(status_code=404, detail="Session not found")

            if user_id not in session.participants:
                result = await self.db.sessions.find_one_and_update(
                    {"id": session_id},
                    {"$addToSet": {"participants": user_id}},
                    return_document=True,
                )

                if not result:
                    raise HTTPException(
                        status_code=404, detail="Session not found during update"
                    )

                session_key = f"quiz_session:{session_id}"
                try:
                    session_data = await self.redis.get(session_key)
                    if session_data:
                        session_obj = QuizSession.model_validate_json(session_data)
                        session_obj.participants.append(user_id)
                        await self.redis.set(
                            session_key, session_obj.model_dump_json(), ex=3600
                        )
                except Exception as e:
                    logger.error(f"Error updating Redis cache: {e}")

                session = QuizSession.model_validate(result)
                logger.info(
                    f"Successfully added participant {user_id} to session {session_id}"
                )

                if notify:
                    await manager.broadcast_to_session(
                        session_id,
                        {
                            "type": "participant_joined",
                            "user_id": user_id,
                            "participants": session.participants,
                        },
                    )

            return session

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error adding participant: {str(e)}")
            raise HTTPException(
                status_code=500, detail=f"Failed to add participant: {str(e)}"
            )

    async def remove_participant(
        self, session_id: str, user_id: str, notify: bool = True
    ) -> QuizSession:
        """Remove participant from session"""
        try:
            if self.db is None:
                raise HTTPException(
                    status_code=500, detail="Database connection not initialized"
                )

            result = await self.db.sessions.find_one_and_update(
                {"id": session_id},
                {"$pull": {"participants": user_id}},
                return_document=True,
            )

            if not result:
                raise HTTPException(status_code=404, detail="Session not found")

            session_key = f"quiz_session:{session_id}"
            try:
                session_data = await self.redis.get(session_key)
                if session_data:
                    session_obj = QuizSession.model_validate_json(session_data)
                    if user_id in session_obj.participants:
                        session_obj.participants.remove(user_id)
                        await self.redis.set(
                            session_key, session_obj.model_dump_json(), ex=3600
                        )
            except Exception as e:
                logger.error(f"Error updating Redis cache: {e}")

            session = QuizSession.model_validate(result)
            logger.info(
                f"Successfully removed participant {user_id} from session {session_id}"
            )
            logger.debug(f"Current participants: {session.participants}")

            if notify:
                await manager.broadcast_to_session(
                    session_id,
                    {
                        "type": "participant_left",
                        "user_id": user_id,
                        "participants": session.participants,
                    },
                )

            return session

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error removing participant: {str(e)}")
            raise HTTPException(
                status_code=500, detail=f"Failed to remove participant: {str(e)}"
            )

    async def get_session(self, session_id: str) -> Optional[QuizSession]:
        """Get session details with retry mechanism"""
        try:
            if self.db is None:
                await self.setup()

            session_key = f"quiz_session:{session_id}"
            session_data = await self.redis.get(session_key)

            if session_data:
                return QuizSession.model_validate_json(session_data)

            session_doc = await self.db.sessions.find_one({"id": session_id})
            if not session_doc:
                return None

            session = QuizSession.model_validate(session_doc)

            try:
                await self.redis.set(
                    session_key, session.model_dump_json(), ex=3600  # 1 hour expiry
                )
            except Exception as e:
                logger.error(f"Error updating Redis cache: {e}")

            return session

        except Exception as e:
            logger.error(f"Error getting session: {str(e)}")
            raise HTTPException(
                status_code=500, detail=f"Failed to get session: {str(e)}"
            )
