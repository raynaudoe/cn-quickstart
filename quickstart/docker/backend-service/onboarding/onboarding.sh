#!/usr/bin/env bash
# Copyright (c) 2026, Digital Asset (Switzerland) GmbH and/or its affiliates.
# SPDX-License-Identifier: 0BSD

# Provision the backend's local Ledger API identity without application party rights.
set -euo pipefail
source /app/utils.sh

if [ "$AUTH_MODE" = "oauth2" ]; then
  backend_user_id="$AUTH_APP_PROVIDER_BACKEND_USER_ID"
else
  backend_user_id="$AUTH_APP_PROVIDER_BACKEND_USER_NAME"
fi

create_user "$APP_PROVIDER_PARTICIPANT_ADMIN_TOKEN" "$backend_user_id" \
  "$AUTH_APP_PROVIDER_BACKEND_USER_NAME" "" "canton:3${PARTICIPANT_JSON_API_PORT_SUFFIX}"

if [ "$AUTH_MODE" = "shared-secret" ]; then
  token=$(generate_jwt "$backend_user_id" "$AUTH_APP_PROVIDER_AUDIENCE")
  share_file "backend-service/on/backend-service.sh" <<EOF
export APP_PROVIDER_BACKEND_USER_TOKEN=${token}
EOF
else
  share_file "backend-service/on/backend-service.sh" <<'EOF'
# OAuth2 client credentials are supplied through the container environment.
EOF
fi
