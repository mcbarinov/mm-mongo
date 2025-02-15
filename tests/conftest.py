import pytest
from pymongo.database import Database

from mm_mongo import MongoConnection


@pytest.fixture
def mongo_database() -> Database:
    conn = MongoConnection.connect("mongodb://localhost/mm-mongo__test")
    conn.client.drop_database(conn.database)

    conn = MongoConnection.connect("mongodb://localhost/mm-mongo__test")
    return conn.database
