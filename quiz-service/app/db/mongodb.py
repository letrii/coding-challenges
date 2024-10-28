from typing import Generator

from app.core.config import get_settings
from pymongo import MongoClient
from pymongo.database import Database
from pymongo.errors import ConnectionFailure

settings = get_settings()


class MongoDB:
    client: MongoClient = None
    db: Database = None

    @classmethod
    def get_client(cls) -> MongoClient:
        if cls.client is None:
            try:
                cls.client = MongoClient(
                    settings.MONGODB_URL,
                    serverSelectionTimeoutMS=5000,
                    connectTimeoutMS=5000,
                )
                cls.client.admin.command("ping")
            except ConnectionFailure as e:
                print(f"Failed to connect to MongoDB: {e}")
                raise
        return cls.client

    @classmethod
    def get_db(cls) -> Database:
        if cls.db is None:
            cls.db = cls.get_client()[settings.MONGODB_DB]
        return cls.db


def get_database() -> Generator[Database, None, None]:
    try:
        db = MongoDB.get_db()
        yield db
    finally:
        pass


def get_collection(collection_name: str):
    return MongoDB.get_db()[collection_name]
