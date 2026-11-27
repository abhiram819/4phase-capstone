import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.models import Base
from app.models import DeviceResponse
from app.repositories.mysql_device_repository import MySqlDeviceRepository
from app.services.device_service import DeviceAlreadyExistsError, DeviceService


@pytest.fixture
def mysql_repository():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield MySqlDeviceRepository(session)
    engine.dispose()


def make_device() -> DeviceResponse:
    return DeviceResponse(
        device_id="router-db-1",
        name="Database router",
        device_type="router",
        ip_address="192.0.2.20",
        location="Lab",
    )


def test_mysql_repository_persists_devices_and_offline_alerts(mysql_repository) -> None:
    service = DeviceService(mysql_repository)

    registered = service.register(make_device())
    assert registered.location == "Lab"
    assert service.get("router-db-1") == registered

    updated = service.update_status("router-db-1", "offline")

    assert updated.status == "offline"
    alerts = mysql_repository.list_alerts()
    assert len(alerts) == 1
    assert alerts[0].device_id == "router-db-1"
    assert alerts[0].timestamp.tzinfo is not None


def test_mysql_repository_translates_duplicate_device_ids(mysql_repository) -> None:
    device = make_device()
    mysql_repository.add_device(device)

    with pytest.raises(DeviceAlreadyExistsError):
        mysql_repository.add_device(device)


def test_mysql_repository_returns_copies_and_missing_updates(mysql_repository) -> None:
    stored = mysql_repository.add_device(make_device())
    stored.name = "Changed outside repository"

    assert mysql_repository.get_device("router-db-1").name == "Database router"
    assert mysql_repository.update_status("missing", "offline") is None