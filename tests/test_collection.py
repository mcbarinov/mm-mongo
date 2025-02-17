import time
from typing import ClassVar

import pytest
from bson import ObjectId
from pymongo import IndexModel
from pymongo.errors import WriteError

from mm_mongo import MongoCollection, MongoModel
from mm_mongo.collection import MongoNotFoundError, drop_collection, mongo_query, parse_indexes, parse_str_index_model


def test_parse_str_index_model():
    assert IndexModel("k").document == parse_str_index_model("k").document
    assert IndexModel("k", unique=True).document == parse_str_index_model("!k").document
    assert IndexModel([("a", 1), ("b", -1)], unique=True).document == parse_str_index_model("!a,-b").document


def test_parse_indexes():
    assert parse_indexes(None) == []
    assert parse_indexes("") == []
    assert [i.document for i in parse_indexes("a")] == [IndexModel("a").document]
    assert [i.document for i in parse_indexes("a, b")] == [IndexModel("a").document, IndexModel("b").document]
    assert [i.document for i in parse_indexes("a,b")] == [IndexModel("a").document, IndexModel("b").document]
    assert [i.document for i in parse_indexes("a,!b")] == [IndexModel("a").document, IndexModel("b", unique=True).document]
    assert [i.document for i in parse_indexes("a, !b")] == [IndexModel("a").document, IndexModel("b", unique=True).document]


def test_mongo_query():
    assert mongo_query(a=1, b=None, c="") == {"a": 1}
    assert mongo_query(a=0) == {"a": 0}


def test_init_collection(database):
    class Data(MongoModel[int]):
        __collection__: str = "test_init_collection__data"
        name: str

    drop_collection(database, Data.__collection__)
    col: MongoCollection[str, Data] = MongoCollection(database, Data)
    col.insert_one(Data(id=1, name="n1"))
    col.insert_one(Data(id=2, name="n2"))
    assert col.count({}) == 2


def test_schema_validation(database):
    class Data(MongoModel[int]):
        name: str
        value: int

        __collection__: str = "data_test_schema_validation"
        __validator__: ClassVar[dict[str, object]] = {
            "$jsonSchema": {"required": ["name", "value"], "properties": {"value": {"minimum": 10}}},
        }

    drop_collection(database, Data.__collection__)
    time.sleep(2)  # without it `-n auto` doesn't work. It looks like drop_collection invokes a little bit later
    col: MongoCollection[int, Data] = MongoCollection(database, Data)
    col.insert_one(Data(id=1, name="n1", value=100))
    with pytest.raises(WriteError):
        col.update_one({"name": "n1"}, {"$set": {"value": 3}})


def test_insert_one(database):
    class Data(MongoModel[int]):
        __collection__: str = "test_insert_one__data"
        name: str

    drop_collection(database, Data.__collection__)
    col: MongoCollection[int, Data] = MongoCollection(database, Data)
    res = col.insert_one(Data(id=1, name="n1"))
    assert res.inserted_id == 1
    assert col.count({}) == 1
    assert col.get(1).name == "n1"


def test_insert_many(database):
    class Data(MongoModel[int]):
        __collection__: str = "test_insert_many__data"
        name: str

    drop_collection(database, Data.__collection__)
    col: MongoCollection[int, Data] = MongoCollection(database, Data)
    docs = [Data(id=1, name="n1"), Data(id=2, name="n2")]
    res = col.insert_many(docs)
    assert res.inserted_ids == [1, 2]
    assert col.count({}) == 2
    assert col.get(1).name == "n1"
    assert col.get(2).name == "n2"


def test_get_or_none(database):
    class Data(MongoModel[int]):
        __collection__: str = "test_get_or_none__data"
        name: str

    drop_collection(database, Data.__collection__)
    col: MongoCollection[int, Data] = MongoCollection(database, Data)
    col.insert_one(Data(id=1, name="n1"))

    assert col.get_or_none(1).name == "n1"
    assert col.get_or_none(2) is None


def test_get(database):
    class Data(MongoModel[int]):
        __collection__: str = "test_get__data"
        name: str

    drop_collection(database, Data.__collection__)
    col: MongoCollection[int, Data] = MongoCollection(database, Data)
    col.insert_one(Data(id=1, name="n1"))

    assert col.get(1).name == "n1"

    with pytest.raises(MongoNotFoundError):
        col.get(2)


def test_find(database):
    class Data(MongoModel[int]):
        __collection__: str = "test_find__data"
        name: str

    drop_collection(database, Data.__collection__)
    col: MongoCollection[int, Data] = MongoCollection(database, Data)
    docs = [Data(id=1, name="n1"), Data(id=2, name="n2"), Data(id=3, name="n3")]
    col.insert_many(docs)

    # Test find all documents
    results = col.find({})
    assert len(results) == 3
    assert results[0].name == "n1"
    assert results[1].name == "n2"
    assert results[2].name == "n3"

    # Test find with query
    results = col.find({"name": "n1"})
    assert len(results) == 1
    assert results[0].name == "n1"

    # Test find with sort
    results = col.find({}, sort="name")
    assert len(results) == 3
    assert results[0].name == "n1"
    assert results[1].name == "n2"
    assert results[2].name == "n3"

    results = col.find({}, sort="-name")
    assert len(results) == 3
    assert results[0].name == "n3"
    assert results[1].name == "n2"
    assert results[2].name == "n1"

    # Test find with limit
    results = col.find({}, limit=2)
    assert len(results) == 2
    assert results[0].name == "n1"
    assert results[1].name == "n2"


def test_find_one(database):
    class Data(MongoModel[int]):
        __collection__: str = "test_find_one__data"
        name: str

    drop_collection(database, Data.__collection__)
    col: MongoCollection[int, Data] = MongoCollection(database, Data)
    docs = [Data(id=1, name="n1"), Data(id=2, name="n2"), Data(id=3, name="n3")]
    col.insert_many(docs)

    # Test find one document
    result = col.find_one({"name": "n1"})
    assert result is not None
    assert result.name == "n1"

    # Test find one document with sort
    result = col.find_one({}, sort="name")
    assert result is not None
    assert result.name == "n1"

    result = col.find_one({}, sort="-name")
    assert result is not None
    assert result.name == "n3"

    # Test find one document with no match
    result = col.find_one({"name": "n4"})
    assert result is None


def test_update_and_get(database):
    class Data(MongoModel[int]):
        __collection__: str = "test_update_and_get__data"
        name: str
        value: int

    drop_collection(database, Data.__collection__)
    col: MongoCollection[int, Data] = MongoCollection(database, Data)
    col.insert_one(Data(id=1, name="n1", value=10))

    # Test update and get
    updated_doc = col.update_and_get(1, {"$set": {"value": 20}})
    assert updated_doc.value == 20

    # Test update and get with non-existing document
    with pytest.raises(MongoNotFoundError):
        col.update_and_get(2, {"$set": {"value": 30}})


def test_set_and_get(database):
    class Data(MongoModel[int]):
        __collection__: str = "test_set_and_get__data"
        name: str
        value: int

    drop_collection(database, Data.__collection__)
    col: MongoCollection[int, Data] = MongoCollection(database, Data)
    col.insert_one(Data(id=1, name="n1", value=10))

    # Test set and get
    updated_doc = col.set_and_get(1, {"value": 20})
    assert updated_doc.value == 20

    # Test set and get with non-existing document
    with pytest.raises(MongoNotFoundError):
        col.set_and_get(2, {"value": 30})


def test_update(database):
    class Data(MongoModel[int]):
        __collection__: str = "test_update__data"
        name: str
        value: int

    drop_collection(database, Data.__collection__)
    col: MongoCollection[int, Data] = MongoCollection(database, Data)
    col.insert_one(Data(id=1, name="n1", value=10))

    # Test update existing document
    update_result = col.update(1, {"$set": {"value": 20}})
    assert update_result.matched_count == 1
    assert update_result.modified_count == 1
    updated_doc = col.get(1)
    assert updated_doc.value == 20

    # Test update non-existing document without upsert
    update_result = col.update(2, {"$set": {"value": 30}})
    assert update_result.matched_count == 0
    assert update_result.modified_count == 0

    # Test update non-existing document with upsert
    update_result = col.update(2, {"$set": {"value": 30, "name": "n2"}}, upsert=True)
    assert update_result.matched_count == 0
    assert update_result.upserted_id == 2
    upserted_doc = col.get(2)
    assert upserted_doc.value == 30


def test_set(database):
    class Data(MongoModel[int]):
        __collection__: str = "test_set__data"
        name: str
        value: int

    drop_collection(database, Data.__collection__)
    col: MongoCollection[int, Data] = MongoCollection(database, Data)
    col.insert_one(Data(id=1, name="n1", value=10))

    # Test set existing document
    update_result = col.set(1, {"value": 20})
    assert update_result.matched_count == 1
    assert update_result.modified_count == 1
    updated_doc = col.get(1)
    assert updated_doc.value == 20

    # Test set non-existing document without upsert
    update_result = col.set(2, {"value": 30})
    assert update_result.matched_count == 0
    assert update_result.modified_count == 0

    # Test set non-existing document with upsert
    update_result = col.set(2, {"value": 30, "name": "n2"}, upsert=True)
    assert update_result.matched_count == 0
    assert update_result.upserted_id == 2
    upserted_doc = col.get(2)
    assert upserted_doc.value == 30
    assert upserted_doc.name == "n2"


def test_set_and_push(database):
    class Data(MongoModel[int]):
        __collection__: str = "test_set_and_push__data"
        name: str
        values: list[int]

    drop_collection(database, Data.__collection__)
    col: MongoCollection[int, Data] = MongoCollection(database, Data)
    col.insert_one(Data(id=1, name="n1", values=[1, 2]))

    # Test set and push
    update_result = col.set_and_push(1, {"name": "n2"}, {"values": 3})
    assert update_result.matched_count == 1
    assert update_result.modified_count == 1
    updated_doc = col.get(1)
    assert updated_doc.name == "n2"
    assert updated_doc.values == [1, 2, 3]

    # Test set and push with non-existing document
    update_result = col.set_and_push(2, {"name": "n3"}, {"values": 4})
    assert update_result.matched_count == 0
    assert update_result.modified_count == 0


def test_update_one(database):
    class Data(MongoModel[int]):
        __collection__: str = "test_update_one__data"
        name: str
        value: int

    drop_collection(database, Data.__collection__)
    col: MongoCollection[int, Data] = MongoCollection(database, Data)
    col.insert_one(Data(id=1, name="n1", value=10))

    # Test update one existing document
    update_result = col.update_one({"_id": 1}, {"$set": {"value": 20}})
    assert update_result.matched_count == 1
    assert update_result.modified_count == 1
    updated_doc = col.get(1)
    assert updated_doc.value == 20

    # Test update one non-existing document without upsert
    update_result = col.update_one({"_id": 2}, {"$set": {"value": 30}})
    assert update_result.matched_count == 0
    assert update_result.modified_count == 0

    # Test update one non-existing document with upsert
    update_result = col.update_one({"_id": 2}, {"$set": {"value": 30, "name": "n2"}}, upsert=True)
    assert update_result.matched_count == 0
    assert update_result.upserted_id == 2
    upserted_doc = col.get(2)
    assert upserted_doc.value == 30
    assert upserted_doc.name == "n2"


def test_update_many(database):
    class Data(MongoModel[ObjectId]):
        __collection__: str = "test_update_many__data"
        name: str
        value: int

    drop_collection(database, Data.__collection__)
    col: MongoCollection[int, Data] = MongoCollection(database, Data)
    id1, id2, id3 = ObjectId(), ObjectId(), ObjectId()
    docs = [
        Data(id=id1, name="n1", value=10),
        Data(id=id2, name="n2", value=20),
        Data(id=id3, name="n1", value=30),
    ]
    col.insert_many(docs)

    # Test update many existing documents
    update_result = col.update_many({"name": "n1"}, {"$set": {"value": 40}})
    assert update_result.matched_count == 2
    assert update_result.modified_count == 2
    assert col.get(id1).value == 40
    assert col.get(id3).value == 40

    # Test update many non-existing documents without upsert
    update_result = col.update_many({"name": "n3"}, {"$set": {"value": 50}})
    assert update_result.matched_count == 0
    assert update_result.modified_count == 0

    # Test update many non-existing documents with upsert
    update_result = col.update_many({"name": "n3"}, {"$set": {"value": 50, "name": "n3"}}, upsert=True)
    assert update_result.matched_count == 0
    assert update_result.upserted_id is not None
    upserted_doc = col.get(update_result.upserted_id)
    assert upserted_doc.value == 50
    assert upserted_doc.name == "n3"


def test_set_many(database):
    class Data(MongoModel[int]):
        __collection__: str = "test_set_many__data"
        name: str
        value: int

    drop_collection(database, Data.__collection__)
    col: MongoCollection[int, Data] = MongoCollection(database, Data)
    docs = [
        Data(id=1, name="n1", value=10),
        Data(id=2, name="n2", value=20),
        Data(id=3, name="n1", value=30),
    ]
    col.insert_many(docs)

    # Test set many existing documents
    update_result = col.set_many({"name": "n1"}, {"value": 40})
    assert update_result.matched_count == 2
    assert update_result.modified_count == 2
    assert col.get(1).value == 40
    assert col.get(3).value == 40

    # Test set many non-existing documents
    update_result = col.set_many({"name": "n3"}, {"value": 50})
    assert update_result.matched_count == 0
    assert update_result.modified_count == 0


def test_delete_many(database):
    class Data(MongoModel[int]):
        __collection__: str = "test_delete_many__data"
        name: str

    drop_collection(database, Data.__collection__)
    col: MongoCollection[int, Data] = MongoCollection(database, Data)
    docs = [Data(id=1, name="n1"), Data(id=2, name="n2"), Data(id=3, name="n1")]
    col.insert_many(docs)

    # Test delete many existing documents
    delete_result = col.delete_many({"name": "n1"})
    assert delete_result.deleted_count == 2
    assert col.count({}) == 1
    assert col.get_or_none(1) is None
    assert col.get_or_none(3) is None
    assert col.get(2).name == "n2"

    # Test delete many non-existing documents
    delete_result = col.delete_many({"name": "n3"})
    assert delete_result.deleted_count == 0
    assert col.count({}) == 1


def test_delete_one(database):
    class Data(MongoModel[int]):
        __collection__: str = "test_delete_one__data"
        name: str

    drop_collection(database, Data.__collection__)
    col: MongoCollection[int, Data] = MongoCollection(database, Data)
    docs = [Data(id=1, name="n1"), Data(id=2, name="n2"), Data(id=3, name="n1")]
    col.insert_many(docs)

    # Test delete one existing document
    delete_result = col.delete_one({"name": "n1"})
    assert delete_result.deleted_count == 1
    assert col.count({}) == 2
    assert col.get_or_none(1) is None or col.get_or_none(3) is None

    # Test delete one non-existing document
    delete_result = col.delete_one({"name": "n3"})
    assert delete_result.deleted_count == 0
    assert col.count({}) == 2


def test_delete(database):
    class Data(MongoModel[int]):
        __collection__: str = "test_delete__data"
        name: str

    drop_collection(database, Data.__collection__)
    col: MongoCollection[int, Data] = MongoCollection(database, Data)
    docs = [Data(id=1, name="n1"), Data(id=2, name="n2"), Data(id=3, name="n3")]
    col.insert_many(docs)

    # Test delete existing document
    delete_result = col.delete(1)
    assert delete_result.deleted_count == 1
    assert col.count({}) == 2
    assert col.get_or_none(1) is None

    # Test delete non-existing document
    delete_result = col.delete(4)
    assert delete_result.deleted_count == 0
    assert col.count({}) == 2


def test_count(database):
    class Data(MongoModel[int]):
        __collection__: str = "test_count__data"
        name: str

    drop_collection(database, Data.__collection__)
    col: MongoCollection[int, Data] = MongoCollection(database, Data)
    docs = [Data(id=1, name="n1"), Data(id=2, name="n2"), Data(id=3, name="n1")]
    col.insert_many(docs)

    # Test count all documents
    assert col.count({}) == 3

    # Test count with query
    assert col.count({"name": "n1"}) == 2
    assert col.count({"name": "n2"}) == 1
    assert col.count({"name": "n3"}) == 0


def test_exists(database):
    class Data(MongoModel[int]):
        __collection__: str = "test_exists__data"
        name: str

    drop_collection(database, Data.__collection__)
    col: MongoCollection[int, Data] = MongoCollection(database, Data)
    docs = [Data(id=1, name="n1"), Data(id=2, name="n2"), Data(id=3, name="n1")]
    col.insert_many(docs)

    # Test exists with existing documents
    assert col.exists({"name": "n1"}) is True
    assert col.exists({"name": "n2"}) is True

    # Test exists with non-existing documents
    assert col.exists({"name": "n3"}) is False


def test_drop_collection(database):
    class Data(MongoModel[int]):
        __collection__: str = "test_drop_collection__data"
        name: str

    drop_collection(database, Data.__collection__)
    col: MongoCollection[int, Data] = MongoCollection(database, Data)
    col.insert_one(Data(id=1, name="n1"))
    assert col.count({}) == 1

    # Test drop collection
    col.drop_collection()
    assert col.count({}) == 0
    assert Data.__collection__ not in database.list_collection_names()


def test_nested_document(database):
    class NestedData(MongoModel[ObjectId]):
        __collection__: str = "test_nested_document__nested_data"
        name: str

    class Data(MongoModel[int]):
        __collection__: str = "test_nested_document__data"
        name: str
        nested: NestedData

    drop_collection(database, NestedData.__collection__)
    drop_collection(database, Data.__collection__)
    col: MongoCollection[int, Data] = MongoCollection(database, Data)
    col.insert_one(Data(id=1, name="n1", nested=NestedData(id=ObjectId(), name="n1")))

    # Test find nested document
    doc = col.get(1)
    assert doc.nested.name == "n1"

    # Test update nested document
    col.update(1, {"$set": {"nested.name": "n2"}})
    doc = col.get(1)
    assert doc.nested.name == "n2"
