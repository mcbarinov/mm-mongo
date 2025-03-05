from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from bson import ObjectId
from pydantic import BaseModel
from pymongo.database import Database
from pymongo.results import DeleteResult, InsertManyResult, InsertOneResult, UpdateResult

type SortType = None | list[tuple[str, int]] | str
type QueryType = Mapping[str, object]
type IdType = str | int | ObjectId
type DocumentType = Mapping[str, Any]
type DatabaseAny = Database[DocumentType]


class MongoUpdateResult[ID: IdType](BaseModel):
    acknowledged: bool
    matched_count: int
    modified_count: int
    upserted_id: ID | None

    @staticmethod
    def from_result(result: UpdateResult) -> MongoUpdateResult[ID]:
        return MongoUpdateResult(
            acknowledged=result.acknowledged,
            matched_count=result.matched_count,
            modified_count=result.modified_count,
            upserted_id=result.upserted_id,
        )


class MongoInsertOneResult[ID: IdType](BaseModel):
    acknowledged: bool
    inserted_id: ID

    @staticmethod
    def from_result(result: InsertOneResult) -> MongoInsertOneResult[ID]:
        return MongoInsertOneResult(acknowledged=result.acknowledged, inserted_id=result.inserted_id)


class MongoInsertManyResult[ID: IdType](BaseModel):
    acknowledged: bool
    inserted_ids: list[ID]

    @staticmethod
    def from_result(result: InsertManyResult) -> MongoInsertManyResult[ID]:
        return MongoInsertManyResult(acknowledged=result.acknowledged, inserted_ids=result.inserted_ids)


class MongoDeleteResult(BaseModel):
    acknowledged: bool
    deleted_count: int

    @staticmethod
    def from_result(result: DeleteResult) -> MongoDeleteResult:
        return MongoDeleteResult(acknowledged=result.acknowledged, deleted_count=result.deleted_count)
