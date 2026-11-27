from pymongo import ReturnDocument
from pymongo.collection import Collection
from pymongo.database import Database
from pymongo.errors import DuplicateKeyError

from app.config import ALERTS_COLLECTION, DEVICES_COLLECTION
from app.db.collections import (
    alert_from_document,
    alert_to_document,
    device_from_document,
    device_to_document,
)
from app.models import AlertResponse, DeviceResponse
from app.repositories.device_repository import DeviceRepository, DeviceStatus
from app.services.errors import DeviceAlreadyExistsError


class MongoDeviceRepository(DeviceRepository):
    def __init__(self, database: Database) -> None:
        self._devices: Collection = database[DEVICES_COLLECTION]
        self._alerts: Collection = database[ALERTS_COLLECTION]

    def add_device(self, device: DeviceResponse) -> DeviceResponse:
        try:
            self._devices.insert_one(device_to_document(device))
        except DuplicateKeyError as error:
            raise DeviceAlreadyExistsError(
                f"Device '{device.device_id}' already exists"
            ) from error
        return device.model_copy(deep=True)

    def list_devices(self) -> list[DeviceResponse]:
        documents = self._devices.find().sort("device_id", 1)
        return [device_from_document(document) for document in documents]

    def get_device(self, device_id: str) -> DeviceResponse | None:
        document = self._devices.find_one({"device_id": device_id})
        return device_from_document(document) if document is not None else None

    def update_status(
        self, device_id: str, status: DeviceStatus
    ) -> DeviceResponse | None:
        document = self._devices.find_one_and_update(
            {"device_id": device_id},
            {"$set": {"status": status}},
            return_document=ReturnDocument.AFTER,
        )
        return device_from_document(document) if document is not None else None

    def save_alert(self, alert: AlertResponse) -> AlertResponse:
        self._alerts.insert_one(alert_to_document(alert))
        return alert.model_copy(deep=True)

    def list_alerts(self) -> list[AlertResponse]:
        documents = self._alerts.find().sort("timestamp", 1)
        return [alert_from_document(document) for document in documents]