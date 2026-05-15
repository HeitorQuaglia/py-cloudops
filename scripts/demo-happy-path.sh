#!/usr/bin/env bash
set -euo pipefail

BUCKET="demo-$(date +%s)"
API_KEY="demo-key-please-change"

echo "==> Disparando criação do bucket '${BUCKET}' via Kong"
RESP=$(curl -sf -X POST "http://localhost:8000/v1/operations" \
  -H "X-API-Key: ${API_KEY}" \
  -H "Content-Type: application/json" \
  -d "{\"operation\":\"create_s3_bucket\",\"parameters\":{\"name\":\"${BUCKET}\",\"type\":\"s3-bucket\",\"owner\":\"team-a\"}}")
echo "API resp: ${RESP}"

CID=$(echo "${RESP}" | python3 -c 'import json,sys; print(json.load(sys.stdin)["correlation_id"])')
echo "==> correlation_id (saga será criada com este ID): ${CID}"

echo "==> Esperando bucket aparecer no LocalStack (até 30s)..."
for i in $(seq 1 60); do
  if docker run --rm --network host \
    -e AWS_ACCESS_KEY_ID=test -e AWS_SECRET_ACCESS_KEY=test -e AWS_DEFAULT_REGION=us-east-1 \
    amazon/aws-cli --endpoint-url=http://localhost:4566 s3 ls "s3://${BUCKET}" >/dev/null 2>&1; then
    echo "==> Bucket existe no LocalStack ✓"
    break
  fi
  sleep 0.5
done

echo "==> Listando recursos no catálogo:"
docker compose exec -T postgres psql -U catalog -d catalog_db -c "SELECT name, state, aws_arn FROM resources WHERE name = '${BUCKET}';"

echo "==> Últimos eventos no audit (MongoDB):"
docker compose exec -T mongodb mongosh --quiet -u "${MONGO_USER:-audit}" -p "${MONGO_PASSWORD:-audit_pw}" --authenticationDatabase admin audit_db \
  --eval "db.events.find({}, {type:1, saga_id:1, _id:0}).sort({occurred_at:1}).limit(20).toArray()"
