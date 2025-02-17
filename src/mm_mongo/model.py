from __future__ import annotations

from collections.abc import Mapping
from typing import ClassVar

from bson import ObjectId
from pydantic import BaseModel, ConfigDict
from pymongo import IndexModel

from mm_mongo.types_ import PKType


class MongoNotFoundError(Exception):
    def __init__(self, pk: object) -> None:
        self.pk = pk
        super().__init__(f"mongo document not found: {pk}")


class MongoModel[ID: PKType](BaseModel):
    model_config = ConfigDict(json_encoders={ObjectId: str})
    id: ID

    __collection__: str
    __validator__: ClassVar[dict[str, object] | None] = None
    __indexes__: ClassVar[list[IndexModel | str] | str] = []

    def to_doc(self) -> Mapping[str, object]:
        doc = self.model_dump()
        if doc["id"] is not None:
            doc["_id"] = doc["id"]
        del doc["id"]
        return doc
