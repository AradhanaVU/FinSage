#!/bin/sh
set -e
# Docker Compose: API_UPSTREAM=api:8000, PORT=80
# Railway: API_UPSTREAM=<api-private-host>:<api-port>, PORT=$PORT
export PORT="${PORT:-80}"
export API_UPSTREAM="${API_UPSTREAM:-api:8000}"
envsubst '${PORT} ${API_UPSTREAM}' < /etc/nginx/templates/default.conf.template > /etc/nginx/conf.d/default.conf
exec nginx -g 'daemon off;'
