import time

import boto3
import httpx
import psycopg
import pymongo
import pytest


pytestmark = pytest.mark.integration


KONG_URL = "http://localhost:8000"
API_KEY = "demo-key-please-change"


def _s3():
    return boto3.client(
        "s3",
        endpoint_url="http://localhost:4566",
        aws_access_key_id="test",
        aws_secret_access_key="test",
        region_name="us-east-1",
    )


def _wait_for(predicate, *, timeout: float = 30.0, interval: float = 0.5, msg: str = ""):
    deadline = time.time() + timeout
    while time.time() < deadline:
        if predicate():
            return
        time.sleep(interval)
    raise AssertionError(f"timeout waiting for: {msg}")


def test_create_s3_bucket_happy_path():
    bucket = f"demo-bucket-{int(time.time())}"

    resp = httpx.post(
        f"{KONG_URL}/v1/operations",
        json={
            "operation": "create_s3_bucket",
            "parameters": {"name": bucket, "type": "s3-bucket", "owner": "team-a"},
        },
        headers={"X-API-Key": API_KEY},
        timeout=5.0,
    )
    assert resp.status_code == 200, resp.text
    correlation_id = resp.json()["correlation_id"]
    assert correlation_id

    def _bucket_exists():
        try:
            _s3().head_bucket(Bucket=bucket)
            return True
        except Exception:
            return False

    _wait_for(_bucket_exists, timeout=30, msg="bucket exists in LocalStack")

    def _catalog_active():
        with psycopg.connect(
            "postgresql://catalog:catalog_pw@localhost:5432/catalog_db"
        ) as conn:
            cur = conn.execute(
                "SELECT state FROM resources WHERE name = %s", (bucket,)
            )
            row = cur.fetchone()
            return row is not None and row[0] == "ACTIVE"

    _wait_for(_catalog_active, timeout=30, msg="catalog.resources ACTIVE")

    def _audit_has_events():
        client = pymongo.MongoClient("mongodb://audit:audit_pw@localhost:27017/?authSource=admin")
        events = list(client["audit_db"]["events"].find())
        client.close()
        return any(e.get("type", "").endswith(".completed") for e in events)

    _wait_for(_audit_has_events, timeout=30, msg="audit has events")
