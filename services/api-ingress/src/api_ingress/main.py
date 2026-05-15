from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import FastAPI, Header
from pydantic import BaseModel

from api_ingress.publisher import get_publisher
from api_ingress.schemas import OperationAccepted, OperationRequest
from cloudops_core.envelope import new_envelope
from cloudops_core.logging import configure_logging, get_logger

configure_logging(service="api-ingress")
log = get_logger()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    await get_publisher()
    yield


app = FastAPI(title="cloudops api-ingress", lifespan=lifespan)


class _Payload(BaseModel):
    operation: str
    parameters: dict


@app.post("/v1/operations", response_model=OperationAccepted)
async def create_operation(
    req: OperationRequest,
    x_correlation_id: str | None = Header(default=None, alias="X-Correlation-ID"),
):
    correlation_id = x_correlation_id or str(uuid4())
    amqp = await get_publisher()

    envelope = new_envelope(
        type_="evt.operation.requested",
        payload=_Payload(operation=req.operation, parameters=req.parameters),
        correlation_id=correlation_id,
    )
    await amqp.publish(exchange="cloudops.events", routing_key="evt.operation.requested", envelope=envelope)
    log.info("operation_requested", correlation_id=correlation_id, operation=req.operation)
    return OperationAccepted(correlation_id=correlation_id)


@app.get("/health")
async def health():
    return {"ok": True}
