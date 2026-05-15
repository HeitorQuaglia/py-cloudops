from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

ALLOWED_OPERATIONS = {"create_s3_bucket"}


class OperationRequest(BaseModel):
    operation: str = Field(..., description="Tipo de operação (ex.: create_s3_bucket)")
    parameters: dict[str, Any] = Field(default_factory=dict)

    @field_validator("operation")
    @classmethod
    def _check_operation(cls, v: str) -> str:
        if v not in ALLOWED_OPERATIONS:
            raise ValueError(f"unknown operation: {v}")
        return v


class OperationAccepted(BaseModel):
    accepted: Literal[True] = True
    correlation_id: str
