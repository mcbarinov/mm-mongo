from collections import OrderedDict
from typing import Any

from bson import CodecOptions
from bson.codec_options import TypeRegistry
from pymongo import ASCENDING, DESCENDING, IndexModel, ReturnDocument
from pymongo.results import DeleteResult, InsertManyResult, InsertOneResult, UpdateResult

from mm_mongo.codecs import DecimalCodec
from mm_mongo.model import MongoModel
from mm_mongo.types_ import DatabaseAny, DocumentType, IdType, QueryType, SortType


class MongoNotFoundError(Exception):
    def __init__(self, id: object) -> None:
        self.id = id
        super().__init__(f"mongo document not found: {id}")


class MongoCollection[ID: IdType, T: MongoModel[Any]]:
    def __init__(self, database: DatabaseAny, model_class: type[T]) -> None:
        if not model_class.__collection__:
            raise ValueError("empty collection name")

        codecs: Any = CodecOptions(type_registry=TypeRegistry([DecimalCodec()]), tz_aware=True)
        self.collection = database.get_collection(model_class.__collection__, codecs)
        if model_class.__indexes__:
            self.collection.create_indexes(parse_indexes(model_class.__indexes__))

        self.model_class = model_class
        if model_class.__validator__:
            # if collection exists
            if model_class.__collection__ in database.list_collection_names():
                query = [("collMod", model_class.__collection__), ("validator", model_class.__validator__)]
                res = database.command(OrderedDict(query))
                if "ok" not in res:
                    raise RuntimeError("can't set schema validator")
            else:
                database.create_collection(model_class.__collection__, codec_options=codecs, validator=model_class.__validator__)

    def insert_one(self, doc: T) -> InsertOneResult:
        return self.collection.insert_one(doc.model_dump())

    def insert_many(self, docs: list[T], ordered: bool = True) -> InsertManyResult:
        return self.collection.insert_many([obj.model_dump() for obj in docs], ordered=ordered)

    def get_or_none(self, id: ID) -> T | None:
        res = self.collection.find_one({"_id": id})
        if res:
            return self._to_model(res)

    def get(self, id: ID) -> T:
        res = self.get_or_none(id)
        if not res:
            raise MongoNotFoundError(id)
        return res

    def find(self, query: QueryType, sort: SortType = None, limit: int = 0) -> list[T]:
        return [self._to_model(d) for d in self.collection.find(query, sort=parse_sort(sort), limit=limit)]

    def find_one(self, query: QueryType, sort: SortType = None) -> T | None:
        res = self.collection.find_one(query, sort=parse_sort(sort))
        if res:
            return self._to_model(res)

    def update_and_get(self, id: ID, update: QueryType) -> T:
        res = self.collection.find_one_and_update({"_id": id}, update, return_document=ReturnDocument.AFTER)
        if res:
            return self._to_model(res)
        raise MongoNotFoundError(id)

    def set_and_get(self, id: ID, update: QueryType) -> T:
        return self.update_and_get(id, {"$set": update})

    def update(self, id: ID, update: QueryType, upsert: bool = False) -> UpdateResult:
        return self.collection.update_one({"_id": id}, update, upsert=upsert)

    def set(self, id: ID, update: QueryType, upsert: bool = False) -> UpdateResult:
        return self.collection.update_one({"_id": id}, {"$set": update}, upsert=upsert)

    def set_and_push(self, id: ID, update: QueryType, push: QueryType) -> UpdateResult:
        return self.collection.update_one({"_id": id}, {"$set": update, "$push": push})

    def update_one(self, query: QueryType, update: QueryType, upsert: bool = False) -> UpdateResult:
        return self.collection.update_one(query, update, upsert=upsert)

    def update_many(self, query: QueryType, update: QueryType, upsert: bool = False) -> UpdateResult:
        return self.collection.update_many(query, update, upsert=upsert)

    def set_many(self, query: QueryType, update: QueryType) -> UpdateResult:
        return self.collection.update_many(query, {"$set": update})

    def delete_many(self, query: QueryType) -> DeleteResult:
        return self.collection.delete_many(query)

    def delete_one(self, query: QueryType) -> DeleteResult:
        return self.collection.delete_one(query)

    def delete(self, id: ID) -> DeleteResult:
        return self.collection.delete_one({"_id": id})

    def count(self, query: QueryType) -> int:
        return self.collection.count_documents(query)

    def exists(self, query: QueryType) -> bool:
        return self.count(query) > 0

    def drop_collection(self) -> None:
        self.collection.drop()

    def _to_model(self, doc: DocumentType) -> T:
        doc["id"] = doc.pop("_id")  # type: ignore[index, attr-defined]
        return self.model_class(**doc)


def parse_sort(sort: SortType) -> list[tuple[str, int]] | None:
    if isinstance(sort, str):
        if sort.startswith("-"):
            return [(sort[1:], -1)]
        return [(sort, 1)]
    return sort


def parse_indexes(value: list[IndexModel | str] | str | None) -> list[IndexModel]:
    if value is None:
        return []
    if isinstance(value, str):
        value = value.strip()
        if value == "":
            return []
        return [parse_str_index_model(index.strip()) for index in value.split(",")]
    return [parse_str_index_model(index) if isinstance(index, str) else index for index in value]


def parse_str_index_model(index: str) -> IndexModel:
    unique = index.startswith("!")
    index = index.removeprefix("!")
    if "," in index:
        keys = []
        for i in index.split(","):
            order = DESCENDING if i.startswith("-") else ASCENDING
            keys.append((i.removeprefix("-"), order))
    else:
        order = DESCENDING if index.startswith("-") else ASCENDING
        index = index.removeprefix("-")
        keys = [(index, order)]
    if unique:
        return IndexModel(keys, unique=True)
    return IndexModel(keys)


def mongo_query(**kwargs: object) -> QueryType:
    return {k: v for k, v in kwargs.items() if v or v == 0}


def drop_collection(database: DatabaseAny, name: str) -> None:
    database.drop_collection(name)
