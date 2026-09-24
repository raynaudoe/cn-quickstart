#!/usr/bin/env bash
# Copyright (c) 2026, Digital Asset (Switzerland) GmbH and/or its affiliates.
# SPDX-License-Identifier: 0BSD
set -euo pipefail

for script in /onboarding/backend-service/on/*.sh; do
  if [ -f "$script" ]; then
    source "$script"
  fi
done

exec node /app/dist/main.js
