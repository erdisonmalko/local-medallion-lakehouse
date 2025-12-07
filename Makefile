# Makefile for local Docker environment

.PHONY: up init down

up:
	@echo "Starting all containers..."
	./scripts/run_local.sh up

init:
	@echo "Initializing environment (MinIO + Postgres)..."
	./scripts/run_local.sh init

down:
	@echo "Stopping all containers..."
	./scripts/run_local.sh down
