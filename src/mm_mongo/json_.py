import json
from dataclasses import asdict, is_dataclass
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from json import JSONEncoder
from typing import Any

from bson import ObjectId
from mm_std import Result
from pydantic import BaseModel
from pymongo.results import DeleteResult, InsertManyResult, InsertOneResult, UpdateResult

from .model import MongoModel


class CustomJSONEncoder(JSONEncoder):
    def default(self, o: Any) -> Any:  # noqa: ANN401
        if isinstance(o, Result):
            return o.to_dict()
        if isinstance(o, MongoModel):
            return o.model_dump()
        if isinstance(o, DeleteResult | UpdateResult):
            return o.raw_result
        if isinstance(o, InsertOneResult):
            return o.inserted_id
        if isinstance(o, InsertManyResult):
            return o.inserted_ids
        if isinstance(o, ObjectId):
            return str(o)
        if isinstance(o, Decimal):
            return str(o)
        if isinstance(o, datetime | date):
            return o.isoformat()
        if is_dataclass(o) and not isinstance(o, type):
            return asdict(o)
        if isinstance(o, Enum):
            return o.value
        if isinstance(o, BaseModel):
            return o.model_dump()
        if isinstance(o, Exception):
            return str(o)
        return JSONEncoder.default(self, o)


def json_dumps(data: object) -> str:
    return json.dumps(data, cls=CustomJSONEncoder)
