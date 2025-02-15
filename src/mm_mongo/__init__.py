from mm_mongo.collection import MongoCollection as MongoCollection
from mm_mongo.connection import MongoConnection as MongoConnection
from mm_mongo.model import MongoModel as MongoModel
from mm_mongo.pydantic import register_object_id_schema

register_object_id_schema()
