#!/usr/bin/env bash
set -euo pipefail
exec 3<>/dev/tcp/127.0.0.1/"${BACKEND_PORT:-8080}"
