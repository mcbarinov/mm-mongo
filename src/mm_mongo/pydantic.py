from collections.abc import Callable

from bson import ObjectId
from pydantic_core import CoreSchema, core_schema


def object_id_validator(v: object) -> ObjectId:
    if isinstance(v, ObjectId):
        return v
    if not ObjectId.is_valid(v):
        raise ValueError("Not a valid ObjectId")
    return ObjectId(v)  # type: ignore[arg-type]


@classmethod  # type: ignore[misc]
def object_id_pydantic_core_schema(cls: type[ObjectId], _source: object, _handler: Callable[[object], CoreSchema]) -> CoreSchema:  # noqa: ARG001
    return core_schema.json_or_python_schema(
        json_schema=core_schema.str_schema(),
        python_schema=core_schema.no_info_plain_validator_function(object_id_validator),
        serialization=core_schema.to_string_ser_schema(),
    )


def monkey_patch_object_id() -> None:
    if hasattr(ObjectId, "__get_pydantic_core_schema__"):
        return

    ObjectId.__get_pydantic_core_schema__ = object_id_pydantic_core_schema  #  type: ignore[attr-defined]
