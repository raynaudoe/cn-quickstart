# Copyright (c) 2026, Digital Asset (Switzerland) GmbH and/or its affiliates.
# SPDX-License-Identifier: 0BSD

SHELL := /bin/bash
.DEFAULT_GOAL := help

include .env
-include .env.local
export AUTH_MODE BACKEND_PORT FRONTEND_PORT APPLICATION_DATABASE PARTY_HINT DOCKER_NETWORK
export DOCKER_CONFIG
export IMAGE_TAG := $(SPLICE_VERSION)
export MODULES_DIR := $(CURDIR)/docker/modules
export LOCALNET_DIR := $(MODULES_DIR)/localnet
export LOCALNET_ENV_DIR := $(LOCALNET_DIR)/env

ifneq ($(AUTH_MODE),shared-secret)
ifneq ($(AUTH_MODE),oauth2)
  $(error AUTH_MODE must be shared-secret or oauth2)
endif
endif
ifneq ($(PQS_ENABLED),true)
ifneq ($(PQS_ENABLED),false)
  $(error PQS_ENABLED must be true or false)
endif
endif

COMPOSE_FILES := -f compose.yaml -f $(LOCALNET_DIR)/compose.yaml
COMPOSE_FILES += -f $(LOCALNET_DIR)/resource-constraints.yaml
COMPOSE_FILES += -f $(MODULES_DIR)/splice-onboarding/compose.yaml
COMPOSE_FILES += -f $(MODULES_DIR)/splice-onboarding/resource-constraints.yaml
COMPOSE_FILES += -f docker/backend-service/resource-constraints.yaml
COMPOSE_ENV := --env-file .env
ifneq ($(wildcard .env.local),)
  COMPOSE_ENV += --env-file .env.local
endif
COMPOSE_ENV += --env-file $(LOCALNET_DIR)/compose.env --env-file $(LOCALNET_ENV_DIR)/common.env
COMPOSE_PROFILES := --profile app-provider --profile app-user --profile sv --profile swagger-ui

ifeq ($(AUTH_MODE),oauth2)
  COMPOSE_FILES += -f $(MODULES_DIR)/keycloak/compose.yaml -f $(MODULES_DIR)/keycloak/resource-constraints.yaml
  COMPOSE_ENV += --env-file $(MODULES_DIR)/keycloak/compose.env
  COMPOSE_PROFILES += --profile keycloak
endif

ifeq ($(PQS_ENABLED),true)
  COMPOSE_FILES += -f $(MODULES_DIR)/pqs/compose.yaml -f $(MODULES_DIR)/pqs/resource-constraints.yaml
  COMPOSE_ENV += --env-file $(MODULES_DIR)/pqs/compose.env
  COMPOSE_PROFILES += --profile pqs-app-provider
endif

COMPOSE = docker compose $(COMPOSE_FILES) $(COMPOSE_ENV) $(COMPOSE_PROFILES)

.PHONY: help setup build check docker-run docker-stop start stop status logs canton-console compose-config clean

help:
	@echo "setup           Create local overrides if missing"
	@echo "build           Build the empty Spring Boot application"
	@echo "check           Build and validate all four Compose configurations"
	@echo "docker-run      Build inside Docker and start the complete application"
	@echo "docker-stop     Stop the stack, preserving database volumes"
	@echo "start           Alias for docker-run"
	@echo "stop            Stop this stack, preserving database volumes"
	@echo "status          Show container status"
	@echo "logs            Show the latest container logs"
	@echo "canton-console  Open the Canton console"
	@echo "compose-config  Render the resolved Compose configuration"
	@echo "clean           Remove Gradle build outputs"

setup:
	@test -f .env.local || cp .env.local.example .env.local

build:
	./gradlew :backend:build --console=plain

check: build
	python3 scripts/test-scaffold.py
	python3 scripts/check-scaffold.py

docker-run:
	$(COMPOSE) up -d --build --wait --wait-timeout 600
	@echo "Application: http://localhost:$(FRONTEND_PORT)"

start: docker-run

docker-stop: stop

stop:
	$(COMPOSE) down

status:
	$(COMPOSE) ps

logs:
	$(COMPOSE) logs --tail=100

canton-console:
	$(COMPOSE) run --build --rm console

compose-config:
	@$(COMPOSE) config $(CONFIG_ARGS)

clean:
	./gradlew clean --console=plain
