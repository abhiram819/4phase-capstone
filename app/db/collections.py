from datetime import timezone
from typing import Any

from pymongo import ASCENDING
from pymongo.database import Database

from app.config import ALERTS_COLLECTION, DEVICES_COLLECTION
from app.models import AlertResponse, DeviceResponse


def device_to_document(device: DeviceResponse) -> dict[str, Any]:
    return device.model_dump(mode="python")


def device_from_document(document: dict[str, Any]) -> DeviceResponse:
    payload = {key: value for key, value in document.items() if key != "_id"}
    return DeviceResponse.model_validate(payload)


def alert_to_document(alert: AlertResponse) -> dict[str, Any]:
    return alert.model_dump(mode="python")


def alert_from_document(document: dict[str, Any]) -> AlertResponse:
    payload = {key: value for key, value in document.items() if key != "_id"}
    timestamp = payload.get("timestamp")
    if timestamp is not None and timestamp.tzinfo is None:
        payload["timestamp"] = timestamp.replace(tzinfo=timezone.utc)
    return AlertResponse.model_validate(payload)


def ensure_indexes(database: Database) -> None:
    devices = database[DEVICES_COLLECTION]
    alerts = database[ALERTS_COLLECTION]
    devices.create_index([("device_id", ASCENDING)], unique=True)
    alerts.create_index([("device_id", ASCENDING)])
    alerts.create_index([("timestamp", ASCENDING)])