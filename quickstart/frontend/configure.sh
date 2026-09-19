#!/bin/sh
set -eu
envsubst '${AUTH_MODE}' < /opt/config.js.template > /usr/share/nginx/html/config.js
