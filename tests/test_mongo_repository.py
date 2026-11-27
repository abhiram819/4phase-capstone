from datetime import datetime, timezone

import pytest
from pymongo.errors import DuplicateKeyError

from app.db.collections import ensure_indexes
from app.models import AlertResponse, DeviceResponse
from app.repositories.mongo_device_repository import MongoDeviceRepository
from app.services.errors import DeviceAlreadyExistsError


class FakeCursor(list):
    def sort(self, key: str, direction: int):
        return FakeCursor(
            sorted(self, key=lambda document: document[key], reverse=direction < 0)
        )


class FakeCollection:
    def __init__(self) -> None:
        self.documents: list[dict] = []
        self.indexes: dict[str, dict] = {}

    def create_index(self, keys, unique: bool = False) -> str:
        name = "_".join(f"{key}_{direction}" for key, direction in keys)
        self.indexes[name] = {"key": keys, "unique": unique}
        return name

    def insert_one(self, document: dict) -> None:
        if "device_id" in document and any(
            existing.get("device_id") == document["device_id"]
            for existing in self.documents
        ):
            raise DuplicateKeyError("duplicate device_id")
        self.documents.append({**document, "_id": len(self.documents) + 1})

    def find(self) -> FakeCursor:
        return FakeCursor(self.documents)

    def find_one(self, query: dict) -> dict | None:
        return next(
            (document for document in self.documents if all(
                document.get(key) == value for key, value in query.items()
            )),
            None,
        )

    def find_one_and_update(self, query: dict, update: dict, return_document=None):
        document = self.find_one(query)
        if document is not None:
            document.update(update["$set"])
        return document


class FakeDatabase:
    def __init__(self) -> None:
        self.collections: dict[str, FakeCollection] = {}

    def __getitem__(self, name: str) -> FakeCollection:
        return self.collections.setdefault(name, FakeCollection())


def make_device(**overrides) -> DeviceResponse:
    values = {
        "device_id": "router-1",
        "name": "Edge router",
        "device_type": "router",
        "ip_address": "192.0.2.10",
    }
    return DeviceResponse(**(values | overrides))


def test_indexes_are_created_for_devices_and_alert_lookups() -> None:
    database = FakeDatabase()

    ensure_indexes(database)
    ensure_indexes(database)

    assert database["devices"].indexes["device_id_1"]["unique"] is True
    assert set(database["alerts"].indexes) == {"device_id_1", "timestamp_1"}


def test_repository_round_trip_hides_mongo_id_and_reads_legacy_location() -> None:
    database = FakeDatabase()
    repository = MongoDeviceRepository(database)
    repository.add_device(make_device())

    stored = repository.get_device("router-1")
    assert stored is not None
    assert stored.location is None
    assert not hasattr(stored, "_id")

    legacy = database["devices"].documents[0]
    legacy.pop("location")
    assert repository.get_device("router-1").location is None


def test_duplicate_device_id_is_translated_to_domain_error() -> None:
    repository = MongoDeviceRepository(FakeDatabase())
    repository.add_device(make_device())

    with pytest.raises(DeviceAlreadyExistsError):
        repository.add_device(make_device())


def test_status_update_and_alert_round_trip() -> None:
    repository = MongoDeviceRepository(FakeDatabase())
    repository.add_device(make_device())

    updated = repository.update_status("router-1", "offline")
    repository.save_alert(
        AlertResponse(
            device_id="router-1",
            message="Device 'router-1' went offline.",
            timestamp=datetime.fromisoformat("2026-11-27T12:00:00+00:00"),
        )
    )
    database = repository._alerts
    database.documents[0]["timestamp"] = datetime(2026, 11, 27, 12, 0)
    alerts = repository.list_alerts()

    assert updated is not None and updated.status == "offline"
    assert repository.update_status("missing", "offline") is None
    assert alerts[0].device_id == "router-1"
    assert alerts[0].timestamp.tzinfo == timezone.utc
    assert not hasattr(alerts[0], "_id")