from collections.abc import Mapping
from typing import Any

from bson import ObjectId
from pymongo.database import Database

type SortType = None | list[tuple[str, int]] | str
type QueryType = Mapping[str, object]
type IdType = str | int | ObjectId
type DocumentType = Mapping[str, Any]
type DatabaseAny = Database[DocumentType]
