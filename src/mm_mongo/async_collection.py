from __future__ import annotations

from collections import OrderedDict
from typing import Any

from pymongo.asynchronous.collection import AsyncCollection, ReturnDocument

from mm_mongo.codecs import codec_options
from mm_mongo.errors import MongoNotFoundError
from mm_mongo.model import MongoModel
from mm_mongo.types_ import (
    AsyncDatabaseAny,
    DocumentType,
    IdType,
    MongoDeleteResult,
    MongoInsertManyResult,
    MongoInsertOneResult,
    MongoUpdateResult,
    QueryType,
    SortType,
)
from mm_mongo.utils import parse_indexes, parse_sort


class AsyncMongoCollection[ID: IdType, T: MongoModel[Any]]:
    def __new__(cls, *_args: object, **_kwargs: object) -> AsyncMongoCollection[ID, T]:
        raise TypeError("Use `AsyncMongoCollection.init()` instead of direct instantiation.")

    def __init__(self, collection: AsyncCollection[DocumentType], model_class: type[T]) -> None:
        self.collection = collection
        self.model_class = model_class

    @classmethod
    async def init(cls, database: AsyncDatabaseAny, model_class: type[T]) -> AsyncMongoCollection[ID, T]:
        instance = super().__new__(cls)

        if not model_class.__collection__:
            raise ValueError("empty collection name")
        instance.collection = database.get_collection(model_class.__collection__, codec_options)
        if model_class.__indexes__:
            await instance.collection.create_indexes(parse_indexes(model_class.__indexes__))
        instance.model_class = model_class

        if model_class.__validator__:
            # if collection exists
            if model_class.__collection__ in await database.list_collection_names():
                query = [("collMod", model_class.__collection__), ("validator", model_class.__validator__)]
                res = await database.command(OrderedDict(query))
                if "ok" not in res:
                    raise RuntimeError("can't set schema validator")
            else:
                await database.create_collection(
                    model_class.__collection__, codec_options=codec_options, validator=model_class.__validator__
                )

        return instance

    async def insert_one(self, doc: T) -> MongoInsertOneResult:
        res = await self.collection.insert_one(doc.model_dump())
        return MongoInsertOneResult.from_result(res)

    async def insert_many(self, docs: list[T], ordered: bool = True) -> MongoInsertManyResult:
        res = await self.collection.insert_many([obj.model_dump() for obj in docs], ordered=ordered)
        return MongoInsertManyResult.from_result(res)

    async def get_or_none(self, id: ID) -> T | None:
        res = await self.collection.find_one({"_id": id})
        if res:
            return self._to_model(res)

    async def get(self, id: ID) -> T:
        res = await self.get_or_none(id)
        if not res:
            raise MongoNotFoundError(id)
        return res

    async def find(self, query: QueryType, sort: SortType = None, limit: int = 0) -> list[T]:
        return [self._to_model(d) async for d in self.collection.find(query, sort=parse_sort(sort), limit=limit)]

    async def find_one(self, query: QueryType, sort: SortType = None) -> T | None:
        res = await self.collection.find_one(query, sort=parse_sort(sort))
        if res:
            return self._to_model(res)

    async def update_and_get(self, id: ID, update: QueryType) -> T:
        res = await self.collection.find_one_and_update({"_id": id}, update, return_document=ReturnDocument.AFTER)
        if res:
            return self._to_model(res)
        raise MongoNotFoundError(id)

    async def set_and_get(self, id: ID, update: QueryType) -> T:
        return await self.update_and_get(id, {"$set": update})

    async def update(self, id: ID, update: QueryType, upsert: bool = False) -> MongoUpdateResult:
        res = await self.collection.update_one({"_id": id}, update, upsert=upsert)
        return MongoUpdateResult.from_result(res)

    async def set(self, id: ID, update: QueryType, upsert: bool = False) -> MongoUpdateResult:
        res = await self.collection.update_one({"_id": id}, {"$set": update}, upsert=upsert)
        return MongoUpdateResult.from_result(res)

    async def push(self, id: ID, push: QueryType) -> MongoUpdateResult:
        res = await self.collection.update_one({"_id": id}, {"$push": push})
        return MongoUpdateResult.from_result(res)

    async def pull(self, id: ID, pull: QueryType) -> MongoUpdateResult:
        res = await self.collection.update_one({"_id": id}, {"$pull": pull})
        return MongoUpdateResult.from_result(res)

    async def set_and_pull(self, id: ID, update: QueryType, pull: QueryType) -> MongoUpdateResult:
        res = await self.collection.update_one({"_id": id}, {"$set": update, "$pull": pull})
        return MongoUpdateResult.from_result(res)

    async def set_and_push(self, id: ID, update: QueryType, push: QueryType) -> MongoUpdateResult:
        res = await self.collection.update_one({"_id": id}, {"$set": update, "$push": push})
        return MongoUpdateResult.from_result(res)

    async def update_one(self, query: QueryType, update: QueryType, upsert: bool = False) -> MongoUpdateResult:
        res = await self.collection.update_one(query, update, upsert=upsert)
        return MongoUpdateResult.from_result(res)

    async def update_many(self, query: QueryType, update: QueryType, upsert: bool = False) -> MongoUpdateResult:
        res = await self.collection.update_many(query, update, upsert=upsert)
        return MongoUpdateResult.from_result(res)

    async def set_many(self, query: QueryType, update: QueryType) -> MongoUpdateResult:
        res = await self.collection.update_many(query, {"$set": update})
        return MongoUpdateResult.from_result(res)

    async def delete_many(self, query: QueryType) -> MongoDeleteResult:
        res = await self.collection.delete_many(query)
        return MongoDeleteResult.from_result(res)

    async def delete_one(self, query: QueryType) -> MongoDeleteResult:
        res = await self.collection.delete_one(query)
        return MongoDeleteResult.from_result(res)

    async def delete(self, id: ID) -> MongoDeleteResult:
        res = await self.collection.delete_one({"_id": id})
        return MongoDeleteResult.from_result(res)

    async def count(self, query: QueryType) -> int:
        return await self.collection.count_documents(query)

    async def exists(self, query: QueryType) -> bool:
        return await self.count(query) > 0

    async def drop_collection(self) -> None:
        await self.collection.drop()

    def _to_model(self, doc: DocumentType) -> T:
        doc["id"] = doc.pop("_id")  # type: ignore[index, attr-defined]
        return self.model_class(**doc)
