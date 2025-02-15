from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlparse

from pymongo import MongoClient

from mm_mongo.types_ import DatabaseAny, DocumentType


@dataclass
class MongoConnection:
    client: MongoClient[DocumentType]
    database: DatabaseAny

    @staticmethod
    def connect(url: str) -> MongoConnection:
        client: MongoClient[DocumentType] = MongoClient(url, tz_aware=True)
        database_name = MongoConnection.get_database_name_from_url(url)
        database = client[database_name]
        return MongoConnection(client=client, database=database)

    @staticmethod
    def get_database_name_from_url(db_url: str) -> str:
        return urlparse(db_url).path[1:]
