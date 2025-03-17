from urllib.parse import urlparse

from pymongo import AsyncMongoClient, MongoClient, WriteConcern

from mm_mongo.types_ import DocumentType


class MongoConnection:
    def __init__(self, url: str, tz_aware: bool = True, write_concern: WriteConcern | None = None) -> None:
        self.client: MongoClient[DocumentType] = MongoClient(url, tz_aware=tz_aware)
        self.database = self.client.get_database(urlparse(url).path[1:], write_concern=write_concern)


class AsyncMongoConnection:
    def __init__(self, url: str, tz_aware: bool = True, write_concern: WriteConcern | None = None) -> None:
        self.client: AsyncMongoClient[DocumentType] = AsyncMongoClient(url, tz_aware=tz_aware)
        self.database = self.client.get_database(urlparse(url).path[1:], write_concern=write_concern)
