from collections.abc import Callable

from bson import ObjectId
from pydantic_core import CoreSchema, core_schema


def register_object_id_schema() -> None:
    def objectid_validator(v: object) -> ObjectId:
        if isinstance(v, ObjectId):
            return v
        if not ObjectId.is_valid(v):
            raise ValueError("Not a valid ObjectId")
        return ObjectId(v)  # type: ignore[arg-type]

    @classmethod  # type: ignore[misc]
    def _get_pydantic_core_schema(cls: type[ObjectId], _source: object, _handler: Callable[[object], CoreSchema]) -> CoreSchema:  # noqa: ARG001
        return core_schema.no_info_plain_validator_function(objectid_validator)

    if getattr(ObjectId, "__get_pydantic_core_schema__", None) is None:
        setattr(ObjectId, "__get_pydantic_core_schema__", _get_pydantic_core_schema)  # noqa: B010
