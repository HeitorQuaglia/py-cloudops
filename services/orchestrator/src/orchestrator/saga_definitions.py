from dataclasses import dataclass


@dataclass(frozen=True)
class Step:
    name: str
    cmd: str
    compensate: str | None = None
    timeout_seconds: int = 30

    @property
    def event_completed(self) -> str:
        return self.cmd.replace("cmd.", "evt.", 1) + ".completed"

    @property
    def event_failed(self) -> str:
        return self.cmd.replace("cmd.", "evt.", 1) + ".failed"


SAGAS: dict[str, list[Step]] = {
    "create_s3_bucket": [
        Step(name="validate",     cmd="cmd.catalog.validate"),
        Step(name="reserve_name", cmd="cmd.catalog.reserve_name", compensate="cmd.catalog.release_name"),
        Step(name="create_bucket",cmd="cmd.provisioning.create_s3_bucket", compensate="cmd.provisioning.delete_s3_bucket"),
        Step(name="register",     cmd="cmd.catalog.register", compensate="cmd.catalog.deregister"),
    ],
}


def get_saga_def(saga_type: str) -> list[Step]:
    if saga_type not in SAGAS:
        raise ValueError(f"unknown saga type: {saga_type}")
    return SAGAS[saga_type]
