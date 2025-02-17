from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlparse

from pymongo import MongoClient, WriteConcern

from mm_mongo.types_ import DatabaseAny, DocumentType


@dataclass
class MongoConnection:
    client: MongoClient[DocumentType]
    database: DatabaseAny

    @staticmethod
    def connect(url: str, tz_aware: bool = True, write_concern: WriteConcern | None = None) -> MongoConnection:
        client: MongoClient[DocumentType] = MongoClient(url, tz_aware=tz_aware)
        database_name = MongoConnection.get_database_name_from_url(url)
        database = client.get_database(database_name, write_concern=write_concern)
        return MongoConnection(client=client, database=database)

    @staticmethod
    def get_database_name_from_url(db_url: str) -> str:
        return urlparse(db_url).path[1:]
