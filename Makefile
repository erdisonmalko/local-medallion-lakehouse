# Makefile for local Docker environment services

.PHONY: up init down

up:
	@echo "Starting all containers..."
	./_scripts/local/run_local.sh up

init:
	@echo "Initializing environment (MinIO + Postgres)..."
	./_scripts/local/run_local.sh init

down:
	@echo "Stopping all containers..."
	./_scripts/local/run_local.sh down
