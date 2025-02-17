import pytest
from pymongo import WriteConcern
from pymongo.database import Database

from mm_mongo import MongoConnection


@pytest.fixture
def database() -> Database:
    write_concern = WriteConcern(w=1)
    conn = MongoConnection.connect("mongodb://localhost/mm-mongo__test", write_concern=write_concern)
    conn.client.drop_database(conn.database)

    conn = MongoConnection.connect("mongodb://localhost/mm-mongo__test", write_concern=write_concern)
    return conn.database
