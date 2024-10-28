import logging
import asyncio
from typing import Dict, Set, Optional
from fastapi import WebSocket, status
from starlette.websockets import WebSocketState

logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self):
        self._active_connections: Dict[str, Dict[str, list[WebSocket]]] = {}
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, session_id: str, user_id: str):
        """Connect a user to a session"""
        async with self._lock:
            try:
                logger.info(
                    f"Adding connection for user {user_id} in session {session_id}"
                )

                if session_id not in self._active_connections:
                    self._active_connections[session_id] = {}

                if user_id not in self._active_connections[session_id]:
                    self._active_connections[session_id][user_id] = []

                for existing_ws in self._active_connections[session_id][user_id]:
                    try:
                        if existing_ws.application_state != WebSocketState.DISCONNECTED:
                            await existing_ws.send_json(
                                {
                                    "type": "connection_closed",
                                    "reason": "New connection established from another location",
                                }
                            )
                            await existing_ws.close(
                                code=status.WS_1008_POLICY_VIOLATION
                            )
                    except Exception as e:
                        logger.error(f"Error closing existing connection: {e}")

                self._active_connections[session_id][user_id] = [websocket]
                logger.info(f"User {user_id} connected to session {session_id}")

            except Exception as e:
                logger.error(f"Error connecting user {user_id}: {e}")
                raise

    async def disconnect(self, websocket: WebSocket, session_id: str, user_id: str):
        """Disconnect a user's WebSocket connection"""
        async with self._lock:
            try:
                logger.info(
                    f"Removing connection for user {user_id} from session {session_id}"
                )

                if session_id in self._active_connections:
                    if user_id in self._active_connections[session_id]:
                        self._active_connections[session_id][user_id] = [
                            ws
                            for ws in self._active_connections[session_id][user_id]
                            if ws != websocket
                        ]

                        if not self._active_connections[session_id][user_id]:
                            logger.info(
                                f"User {user_id} has no more connections, removing from session {session_id}"
                            )
                            del self._active_connections[session_id][user_id]

                            if not self._active_connections[session_id]:
                                del self._active_connections[session_id]

                            return True

                return False

            except Exception as e:
                logger.error(f"Error disconnecting user {user_id}: {e}")
                return False

    def get_user_connection_count(self, session_id: str, user_id: str) -> int:
        """Get number of active connections for a user"""
        return len(self._active_connections.get(session_id, {}).get(user_id, []))

    async def broadcast_to_session(
        self, session_id: str, message: dict, exclude_user: Optional[str] = None
    ):
        """Broadcast a message to all users in a session"""
        if session_id not in self._active_connections:
            return

        for user_id, connections in self._active_connections[session_id].items():
            if exclude_user and user_id == exclude_user:
                continue

            for connection in connections:
                try:
                    if connection.application_state != WebSocketState.DISCONNECTED:
                        await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Error sending message to user {user_id}: {e}")
                    asyncio.create_task(
                        self.disconnect(connection, session_id, user_id)
                    )

    def get_session_participants(self, session_id: str) -> Set[str]:
        """Get all participants in a session"""
        return set(self._active_connections.get(session_id, {}).keys())


manager = ConnectionManager()
