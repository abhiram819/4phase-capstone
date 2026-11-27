from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.config import DATABASE_BACKEND
from app.db.session import get_db
from app.models import AlertResponse, DeviceCreate, DeviceResponse, StatusUpdate
from app.repositories.device_repository import DeviceRepository, InMemoryDeviceRepository
from app.repositories.mysql_device_repository import MySqlDeviceRepository
from app.services.device_service import (
    DeviceAlreadyExistsError,
    DeviceNotFoundError,
    DeviceService,
)

router = APIRouter()
memory_repository = InMemoryDeviceRepository()


def get_repository(
    database: Session = Depends(get_db),
) -> DeviceRepository:
    if DATABASE_BACKEND == "mysql":
        return MySqlDeviceRepository(database)
    if DATABASE_BACKEND != "memory":
        raise ValueError("DATABASE_BACKEND must be either 'memory' or 'mysql'")
    return memory_repository


def get_device_service(
    repository: DeviceRepository = Depends(get_repository),
) -> DeviceService:
    return DeviceService(repository)


@router.post(
    "/devices",
    response_model=DeviceResponse,
    status_code=status.HTTP_201_CREATED,
    responses={409: {"description": "A device with this ID already exists"}},
)
def register_device(
    payload: DeviceCreate,
    device_service: DeviceService = Depends(get_device_service),
) -> DeviceResponse:
    try:
        return device_service.register(payload)
    except DeviceAlreadyExistsError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(error)
        ) from error


@router.get("/devices", response_model=list[DeviceResponse])
def list_devices(
    device_service: DeviceService = Depends(get_device_service),
) -> list[DeviceResponse]:
    return device_service.list()


@router.get(
    "/devices/{device_id}",
    response_model=DeviceResponse,
    responses={404: {"description": "Device not found"}},
)
def get_device(
    device_id: str,
    device_service: DeviceService = Depends(get_device_service),
) -> DeviceResponse:
    try:
        return device_service.get(device_id)
    except DeviceNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(error)
        ) from error


@router.patch(
    "/devices/{device_id}/status",
    response_model=DeviceResponse,
    responses={404: {"description": "Device not found"}},
)
def update_device_status(
    device_id: str,
    payload: StatusUpdate,
    device_service: DeviceService = Depends(get_device_service),
) -> DeviceResponse:
    try:
        return device_service.update_status(device_id, payload.status)
    except DeviceNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(error)
        ) from error


@router.get("/alerts", response_model=list[AlertResponse])
def list_alerts(
    repository: DeviceRepository = Depends(get_repository),
) -> list[AlertResponse]:
    return repository.list_alerts()


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}