from abc import ABC, abstractmethod
from logging import getLogger
from os import environ
from uuid import uuid4

from bson.objectid import ObjectId
from pymongo import ASCENDING, MongoClient

from definitions import APP_ENV, ENV_DEV, ENV_PROD, COLLECTIONS, MONGODB_CONNECTION, MONGO_DATABASE, MONGODB_HOSTNAME, \
    MONGO_USERNAME, MONGO_PASSWORD

logger = getLogger(__name__)


class Repository(ABC):
    @abstractmethod
    def get(self, collection_name, filter=None, **kwargs):
        pass

    @abstractmethod
    def get_many(self, collection_name, filter=None, **kwargs) -> list:
        pass

    @abstractmethod
    def save(self, collection_name, filter, item) -> None:
        pass

    @abstractmethod
    def save_many(self, collection_name, items) -> None:
        pass

    @abstractmethod
    def delete(self, collection_name, item) -> None:
        pass


class RegularRepository(Repository):
    def __init__(self, uri):
        self.mongo_client = MongoClient(host=uri, connect=False)
        self.database = self.mongo_client.get_default_database()
        self._create_indexes()

    def _create_indexes(self):
        self.database["cities"].create_index([("cityName", ASCENDING)])
        self.database["countries"].create_index([("countryCode", ASCENDING)])
        self.database["sensors"].create_index([("sensorId", ASCENDING)])
        self.database["predictions"].create_index([("cityName", ASCENDING), ("sensorId", ASCENDING)])
        for collection in COLLECTIONS:
            self.database[collection].create_index([("sensorId", ASCENDING)])

    def get(self, collection_name, filter=None, **kwargs):
        collection = self.database[collection_name]
        document = collection.find_one(filter=filter, **kwargs)
        return document if document else None

    def get_many(self, collection_name, filter=None, **kwargs) -> list:
        collection = self.database[collection_name]
        documents = collection.find(filter, **kwargs)
        return list(documents)

    def save(self, collection_name, filter, item) -> None:
        collection = self.database[collection_name]
        if filter is None:
            # Insert new item
            collection.insert_one(item if isinstance(item, dict) else item.__dict__)
        else:
            # Update existing item
            collection.replace_one(filter=filter, replacement=item if isinstance(item, dict) else item.__dict__,
                                   upsert=True)

    def save_many(self, collection_name, items) -> None:
        collection = self.database[collection_name]
        documents = [item if isinstance(item, dict) else item.__dict__ for item in items]
        results = collection.insert_many(documents)
        for item, result in zip(items, results.inserted_ids):
            if isinstance(item, dict):
                item["_id"] = str(result)
            else:
                item.id = str(result)

    def delete(self, collection_name, item) -> None:
        collection = self.database[collection_name]
        if item.id is not None:
            collection.delete_one({"_id": ObjectId(item.id)})


class InMemoryRepository(Repository):
    def __init__(self):
        self.collections = {}

    def get(self, collection_name, filter=None, **kwargs):
        collection = self.collections.get(collection_name, [])
        if filter:
            for item in collection:
                if all(item.get(key) == value for key, value in filter.items()):
                    return item
        return None

    def get_many(self, collection_name, filter=None, **kwargs) -> list:
        collection = self.collections.get(collection_name, {})
        if filter:
            return [item for item in collection.values() if self._matches_filter(item, filter)]
        return list(collection.values())

    def save(self, collection_name, filter, item) -> None:
        collection = self.collections.setdefault(collection_name, {})
        if isinstance(item, dict):
            self._save_dict_item(collection, filter, item)
        else:
            self._save_class_item(collection, filter, item)

    def _save_dict_item(self, collection, filter, item):
        if filter is None:
            item_id = item.get("_id") or str(uuid4())
            item["_id"] = item_id
            collection[item_id] = item
        else:
            existing_item = next((existing_item for existing_item in collection.values()
                                  if all(existing_item.get(k) == v for k, v in filter.items())), None)
            if existing_item:
                existing_item.update(item)
            else:
                item_id = item.get("_id") or str(uuid4())
                item["_id"] = item_id
                collection[item_id] = item

    def _save_class_item(self, collection, filter, item):
        if filter is None:
            item_id = item.id or str(uuid4())
            item.id = item_id
            collection[item_id] = item
        else:
            existing_item = next((existing_item for existing_item in collection.values()
                                  if all(existing_item.__dict__.get(k) == v for k, v in filter.items())), None)
            if existing_item:
                existing_item.__dict__.update(item.__dict__)
            else:
                item_id = item.id or str(uuid4())
                item.id = item_id
                collection[item_id] = item

    def save_many(self, collection_name, items) -> None:
        for item in items:
            self.save(collection_name=collection_name, filter=None, item=item)

    def delete(self, collection_name, item) -> None:
        collection = self.collections.get(collection_name, {})
        if isinstance(item, dict):
            if item["_id"] in collection:
                del collection[item["_id"]]
        else:
            if item.id in collection:
                del collection[item.id]

    @staticmethod
    def _matches_filter(item, filter) -> bool:
        for key, value in filter.items():
            if key not in item.__dict__ or item.__dict__[key] != value:
                return False
        return True


class RepositorySingleton:
    _instance = None
    _repository = None

    @staticmethod
    def get_instance():
        if not RepositorySingleton._instance:
            RepositorySingleton._instance = RepositorySingleton()
        return RepositorySingleton._instance

    def __init__(self):
        if not RepositorySingleton._repository:
            if environ.get(APP_ENV, ENV_DEV) == ENV_PROD:
                RepositorySingleton._repository = RegularRepository(
                    f"{environ[MONGODB_CONNECTION]}://{environ[MONGO_USERNAME]}:{environ[MONGO_PASSWORD]}@"
                    f"{environ[MONGODB_HOSTNAME]}/{environ[MONGO_DATABASE]}"
                    f"?authSource=admin&retryWrites=true&w=majority")
            else:
                RepositorySingleton._repository = InMemoryRepository()

    @staticmethod
    def get_repository() -> Repository:
        return RepositorySingleton._repository
