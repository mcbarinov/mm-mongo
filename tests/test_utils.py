from pymongo import IndexModel

from mm_mongo import mongo_query
from mm_mongo.utils import parse_indexes, parse_sort, parse_str_index_model


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


def test_parse_sort():
    assert parse_sort("a") == [("a", 1)]
    assert parse_sort("-a") == [("a", -1)]
    assert parse_sort("a,b") == [("a", 1), ("b", 1)]
    assert parse_sort("a, b") == [("a", 1), ("b", 1)]
    assert parse_sort("a,-b") == [("a", 1), ("b", -1)]
    assert parse_sort("-a,-b") == [("a", -1), ("b", -1)]
    assert parse_sort([("a", 1), ("b", -1)]) == [("a", 1), ("b", -1)]
    assert parse_sort(None) is None
