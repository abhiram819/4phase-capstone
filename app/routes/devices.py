from fastapi import APIRouter, HTTPException, status

from app.models import AlertResponse, DeviceCreate, DeviceResponse, StatusUpdate
from app.repositories.device_repository import InMemoryDeviceRepository
from app.services.device_service import (
    DeviceAlreadyExistsError,
    DeviceNotFoundError,
    DeviceService,
)

router = APIRouter()
repository = InMemoryDeviceRepository()
device_service = DeviceService(repository)


@router.post(
    "/devices",
    response_model=DeviceResponse,
    status_code=status.HTTP_201_CREATED,
    responses={409: {"description": "A device with this ID already exists"}},
)
def register_device(payload: DeviceCreate) -> DeviceResponse:
    try:
        return device_service.register(payload)
    except DeviceAlreadyExistsError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(error)
        ) from error


@router.get("/devices", response_model=list[DeviceResponse])
def list_devices() -> list[DeviceResponse]:
    return device_service.list()


@router.get(
    "/devices/{device_id}",
    response_model=DeviceResponse,
    responses={404: {"description": "Device not found"}},
)
def get_device(device_id: str) -> DeviceResponse:
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
def update_device_status(device_id: str, payload: StatusUpdate) -> DeviceResponse:
    try:
        return device_service.update_status(device_id, payload.status)
    except DeviceNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(error)
        ) from error


@router.get("/alerts", response_model=list[AlertResponse])
def list_alerts() -> list[AlertResponse]:
    return repository.list_alerts()


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}