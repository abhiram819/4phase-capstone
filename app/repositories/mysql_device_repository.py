from datetime import timezone

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.models import AlertRecord, DeviceRecord
from app.models import AlertResponse, DeviceResponse
from app.repositories.device_repository import DeviceRepository, DeviceStatus
from app.services.errors import DeviceAlreadyExistsError


class MySqlDeviceRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add_device(self, device: DeviceResponse) -> DeviceResponse:
        record = DeviceRecord(
            device_id=device.device_id,
            name=device.name,
            device_type=device.device_type,
            ip_address=device.ip_address,
            status=device.status,
            location=device.location,
        )
        self._session.add(record)
        try:
            self._session.commit()
        except IntegrityError as error:
            self._session.rollback()
            raise DeviceAlreadyExistsError(
                f"Device '{device.device_id}' already exists"
            ) from error
        self._session.refresh(record)
        return self._to_device_response(record)

    def list_devices(self) -> list[DeviceResponse]:
        records = self._session.scalars(
            select(DeviceRecord).order_by(DeviceRecord.device_id)
        ).all()
        return [self._to_device_response(record) for record in records]

    def get_device(self, device_id: str) -> DeviceResponse | None:
        record = self._session.scalar(
            select(DeviceRecord).where(DeviceRecord.device_id == device_id)
        )
        return self._to_device_response(record) if record is not None else None

    def update_status(
        self, device_id: str, status: DeviceStatus
    ) -> DeviceResponse | None:
        record = self._session.scalar(
            select(DeviceRecord).where(DeviceRecord.device_id == device_id)
        )
        if record is None:
            return None
        record.status = status
        try:
            self._session.commit()
        except Exception:
            self._session.rollback()
            raise
        self._session.refresh(record)
        return self._to_device_response(record)

    def save_alert(self, alert: AlertResponse) -> AlertResponse:
        record = AlertRecord(
            device_id=alert.device_id,
            message=alert.message,
            timestamp=alert.timestamp,
        )
        self._session.add(record)
        try:
            self._session.commit()
        except Exception:
            self._session.rollback()
            raise
        self._session.refresh(record)
        return self._to_alert_response(record)

    def list_alerts(self) -> list[AlertResponse]:
        records = self._session.scalars(
            select(AlertRecord).order_by(AlertRecord.id)
        ).all()
        return [self._to_alert_response(record) for record in records]

    @staticmethod
    def _to_device_response(record: DeviceRecord) -> DeviceResponse:
        return DeviceResponse(
            device_id=record.device_id,
            name=record.name,
            device_type=record.device_type,
            ip_address=record.ip_address,
            status=record.status,
            location=record.location,
        )

    @staticmethod
    def _to_alert_response(record: AlertRecord) -> AlertResponse:
        timestamp = record.timestamp
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=timezone.utc)
        return AlertResponse(
            device_id=record.device_id,
            message=record.message,
            timestamp=timestamp,
        )