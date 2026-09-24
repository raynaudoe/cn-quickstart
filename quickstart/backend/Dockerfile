# Copyright (c) 2026, Digital Asset (Switzerland) GmbH and/or its affiliates.
# SPDX-License-Identifier: 0BSD
FROM node:24-bookworm-slim@sha256:2fe369e969550cde8e867afc3fe370b260140cab4a23d467074295b42163d553 AS base
WORKDIR /app

FROM base AS build
COPY backend/package.json backend/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY backend/tsconfig.json ./
COPY backend/src ./src
RUN npm run build && npm prune --omit=dev

FROM base
ENV NODE_ENV=production
COPY --from=build /app/package.json ./package.json
COPY --from=build /app/node_modules ./node_modules
COPY --from=build /app/dist ./dist
COPY --chmod=755 docker/backend-service/start.sh ./start.sh
COPY --chmod=755 docker/backend-service/healthcheck.sh ./healthcheck.sh
USER node
CMD ["/app/start.sh"]
