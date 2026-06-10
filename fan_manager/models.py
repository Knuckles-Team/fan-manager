"""Pydantic models for Fan Manager tool inputs and outputs."""

from pydantic import BaseModel, Field


class CommandResult(BaseModel):
    """Standard result envelope returned by fan-manager operations."""

    response: object | None = Field(
        default=None, description="The primary result payload (e.g., a temperature)."
    )
    command: str = Field(description="The underlying shell command that was executed.")
    status: int = Field(description="HTTP-style status code (200 ok, 4xx/5xx error).")
    error: str | None = Field(
        default=None, description="Error message when status indicates a failure."
    )


class TempReading(CommandResult):
    """Result of a temperature read (CONCEPT:FAN-001)."""


class FanSetResult(CommandResult):
    """Result of a fan-speed change (CONCEPT:FAN-002)."""


class SetFanInput(BaseModel):
    """Input for setting a fixed fan level (CONCEPT:FAN-002)."""

    fan_level: int = Field(ge=0, le=100, description="Fan speed level (0-100).")


class AutoFanInput(BaseModel):
    """Input for automatic temperature-driven fan control (CONCEPT:FAN-002)."""

    minimum_fan_speed: float = Field(default=5, ge=0, le=100)
    maximum_fan_speed: float = Field(default=100, ge=0, le=100)
    minimum_temperature: float = Field(default=50, ge=0, le=120)
    maximum_temperature: float = Field(default=80, ge=0, le=120)
    temperature_power: int = Field(default=5, ge=0, le=10)
