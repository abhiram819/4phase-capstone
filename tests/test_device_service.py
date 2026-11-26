from datetime import timezone

import pytest

from app.models import DeviceCreate
from app.repositories.device_repository import InMemoryDeviceRepository
from app.services.device_service import (
    DeviceAlreadyExistsError,
    DeviceNotFoundError,
    DeviceService,
)


@pytest.fixture
def device_context() -> tuple[InMemoryDeviceRepository, DeviceService]:
    repository = InMemoryDeviceRepository()
    return repository, DeviceService(repository)


def make_device(status: str = "online") -> DeviceCreate:
    return DeviceCreate(
        device_id="router-1",
        name="Edge router",
        device_type="router",
        ip_address="192.0.2.10",
        status=status,
    )


def test_registers_device(device_context) -> None:
    _, service = device_context

    device = service.register(make_device())

    assert device.device_id == "router-1"
    assert device.status == "online"
    assert service.get("router-1") == device


def test_duplicate_device_id_raises_error(device_context) -> None:
    _, service = device_context
    service.register(make_device())

    with pytest.raises(DeviceAlreadyExistsError):
        service.register(make_device())


def test_missing_device_raises_error(device_context) -> None:
    _, service = device_context

    with pytest.raises(DeviceNotFoundError):
        service.get("missing-device")


def test_initial_offline_registration_creates_no_alert(device_context) -> None:
    repository, service = device_context

    device = service.register(make_device(status="offline"))

    assert device.status == "offline"
    assert repository.list_alerts() == []


def test_online_to_offline_creates_one_alert(device_context) -> None:
    repository, service = device_context
    service.register(make_device())

    service.update_status("router-1", "offline")

    alerts = repository.list_alerts()
    assert len(alerts) == 1
    assert alerts[0].device_id == "router-1"
    assert alerts[0].message == "Device 'router-1' went offline."
    assert alerts[0].timestamp.tzinfo == timezone.utc


def test_repeated_offline_update_does_not_create_another_alert(device_context) -> None:
    repository, service = device_context
    service.register(make_device())
    service.update_status("router-1", "offline")

    service.update_status("router-1", "offline")

    assert len(repository.list_alerts()) == 1