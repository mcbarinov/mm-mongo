from pymongo import ASCENDING, DESCENDING, IndexModel

from mm_mongo.types import SortType


def parse_sort(sort: SortType) -> list[tuple[str, int]] | None:
    if isinstance(sort, str):
        result = []
        for field in sort.split(","):
            field = field.strip()  # noqa: PLW2901
            if field.startswith("-"):
                result.append((field[1:], -1))
            else:
                result.append((field, 1))
        return result
    return sort


def parse_indexes(value: list[IndexModel | str] | str | None) -> list[IndexModel]:
    """Parse index definitions from various formats.

    Supports:
    - Single field: "field" (ascending), "-field" (descending), "!field" (unique)
    - Compound index: "!field1:-field2:field3" (unique compound index)
    - Multiple indexes: "field1, !field2:-field3, -field4"

    Args:
        value: Index definitions as string, list, or None

    Returns:
        List of IndexModel objects
    """
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
    if ":" in index:
        keys = []
        for i in index.split(":"):
            order = DESCENDING if i.startswith("-") else ASCENDING
            keys.append((i.removeprefix("-"), order))
    else:
        order = DESCENDING if index.startswith("-") else ASCENDING
        index = index.removeprefix("-")
        keys = [(index, order)]
    if unique:
        return IndexModel(keys, unique=True)
    return IndexModel(keys)
