# py-cloudops

Projeto educacional: microsserviços event-driven com SAGA Pattern para automação Cloud/SRE.

## Stack
Python 3.12, FastAPI, RabbitMQ, PostgreSQL, MongoDB, LocalStack, Kong.

## Como rodar (Iteração 1)
```bash
make up           # sobe toda a stack
make demo-happy   # dispara um POST que cria um bucket S3 no LocalStack
make logs         # logs agregados
make down
```

Ver `docs/superpowers/specs/` para o design completo (local, não versionado).
