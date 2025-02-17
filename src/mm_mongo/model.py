from __future__ import annotations

from collections.abc import Callable
from typing import ClassVar

from bson import ObjectId
from pydantic import BaseModel, ConfigDict, model_serializer, model_validator
from pydantic_core.core_schema import SerializationInfo
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

    @model_serializer(mode="wrap")
    def serialize_model(self, serializer: Callable[[object], dict[str, object]], _info: SerializationInfo) -> dict[str, object]:
        data = serializer(self)
        if data.get("id") is not None:
            data["_id"] = data["id"]
            del data["id"]
        return data

    @model_validator(mode="before")
    @classmethod
    def restore_id(cls, values: dict[str, object]) -> dict[str, object]:
        """
        Pre-validate the input data. If '_id' exists, move its value to 'id'.
        """
        if isinstance(values, dict) and "_id" in values:
            values["id"] = values.pop("_id")
        return values

    # def to_doc(self) -> Mapping[str, object]:
    #     doc = self.model_dump()
    #     if doc["id"] is not None:
    #         doc["_id"] = doc["id"]
    #     del doc["id"]
    #     return doc
