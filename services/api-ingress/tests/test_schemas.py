import pytest

from api_ingress.schemas import OperationRequest


def test_request_valid():
    req = OperationRequest(operation="create_s3_bucket", parameters={"name": "b1", "type": "s3-bucket", "owner": "team-a"})
    assert req.operation == "create_s3_bucket"


def test_request_rejects_unknown_operation():
    with pytest.raises(ValueError):
        OperationRequest(operation="rm_dash_rf", parameters={})
