import random
import string

import pytest
import pytest_asyncio
from pymongo import WriteConcern

from mm_mongo import AsyncMongoConnection, MongoConnection


@pytest.fixture
def database():
    rnd_suffix = "".join(random.choices(string.ascii_letters + string.digits, k=32))
    url = f"mongodb://localhost/mm-mongo__test_{rnd_suffix}"
    conn = MongoConnection(url, write_concern=WriteConcern(w=1))
    yield conn.database
    conn.client.drop_database(conn.database.name)


@pytest_asyncio.fixture
async def async_database():
    rnd_suffix = "".join(random.choices(string.ascii_letters + string.digits, k=32))
    url = f"mongodb://localhost/mm-mongo__test_{rnd_suffix}"
    conn = AsyncMongoConnection(url, write_concern=WriteConcern(w=1))
    yield conn.database
    await conn.client.drop_database(conn.database.name)
