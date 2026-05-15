from datetime import datetime, timezone
from uuid import uuid4

from pydantic import BaseModel

from cloudops_core.envelope import Envelope, new_envelope


class CreateBucketPayload(BaseModel):
    name: str
    region: str


def test_new_envelope_sets_metadata_defaults():
    payload = CreateBucketPayload(name="my-bucket", region="us-east-1")
    env = new_envelope(
        type_="cmd.provisioning.create_s3_bucket",
        payload=payload,
        correlation_id="saga-123",
    )

    assert env.type == "cmd.provisioning.create_s3_bucket"
    assert env.correlation_id == "saga-123"
    assert env.causation_id is None
    assert env.version == 1
    assert isinstance(env.occurred_at, datetime)
    assert env.occurred_at.tzinfo is not None
    assert env.payload.name == "my-bucket"


def test_envelope_roundtrip_json():
    payload = CreateBucketPayload(name="b", region="us-east-1")
    env = new_envelope(
        type_="cmd.provisioning.create_s3_bucket",
        payload=payload,
        correlation_id="saga-x",
        causation_id="prev-msg",
    )

    raw = env.model_dump_json()
    parsed = Envelope[CreateBucketPayload].model_validate_json(raw)
    assert parsed.message_id == env.message_id
    assert parsed.payload.name == "b"
    assert parsed.causation_id == "prev-msg"
