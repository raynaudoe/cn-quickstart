FROM node:22-alpine AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY src ./src
COPY public ./public
COPY test ./test
RUN npm test && npm run build

FROM nginx:1.27.0-alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf.template /etc/nginx/templates/default.conf.template
COPY config.js.template /opt/config.js.template
COPY --chmod=755 configure.sh /docker-entrypoint.d/30-configure-app.sh
