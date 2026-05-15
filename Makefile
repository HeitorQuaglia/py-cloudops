SHELL := /bin/bash
.PHONY: help up down logs build test test-int demo-happy seed clean

help:
	@echo "Targets:"
	@echo "  up              Sobe toda a stack (docker compose)"
	@echo "  down            Derruba a stack (preserva volumes)"
	@echo "  clean           Derruba e apaga volumes"
	@echo "  build           Builda imagens dos serviços"
	@echo "  logs            Tail dos logs (use SERVICE=<name> para filtrar)"
	@echo "  test            Roda testes unitários de todos os pacotes"
	@echo "  test-int        Roda testes de integração contra a stack rodando"
	@echo "  demo-happy      Executa demo: cria um bucket S3 via fluxo SAGA completo"
	@echo "  seed            Garante .env existe (a partir de .env.example)"

seed:
	@test -f .env || cp .env.example .env

up: seed
	docker compose up -d --build

down:
	docker compose down

clean:
	docker compose down -v

build:
	docker compose build

logs:
ifeq ($(SERVICE),)
	docker compose logs -f --tail=200
else
	docker compose logs -f --tail=200 $(SERVICE)
endif

test:
	uv run python -m pytest libs/cloudops-core/tests -v -m "not integration"
	uv run python -m pytest services/catalog/tests -v -m "not integration"
	uv run python -m pytest services/provisioning/tests -v -m "not integration"
	uv run python -m pytest services/audit/tests -v -m "not integration"
	uv run python -m pytest services/orchestrator/tests -v -m "not integration"
	uv run python -m pytest services/api-ingress/tests -v -m "not integration"

test-int:
	uv run pytest tests/integration -v

demo-happy:
	bash scripts/demo-happy-path.sh
