from datetime import datetime
from ipaddress import IPv4Address
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class DeviceFields(BaseModel):
    device_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    device_type: Literal["router", "switch", "server"]
    ip_address: str
    status: Literal["online", "offline"] = "online"
    location: str | None = None

    @field_validator("ip_address")
    @classmethod
    def validate_ipv4(cls, value: str) -> str:
        try:
            IPv4Address(value)
        except ValueError as error:
            raise ValueError("ip_address must be a valid IPv4 address") from error
        return value


class DeviceCreate(DeviceFields):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "device_id": "router-01",
                    "name": "Branch Router",
                    "device_type": "router",
                    "ip_address": "192.0.2.10",
                    "status": "online",
                }
            ]
        }
    )


class DeviceResponse(DeviceFields):
    pass


class StatusUpdate(BaseModel):
    model_config = ConfigDict(json_schema_extra={"examples": [{"status": "offline"}]})

    status: Literal["online", "offline"]


class AlertResponse(BaseModel):
    device_id: str
    message: str
    timestamp: datetime