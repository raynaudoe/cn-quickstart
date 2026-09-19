ARG JAVA_VERSION=21-jdk
FROM eclipse-temurin:${JAVA_VERSION} AS build
WORKDIR /workspace
COPY gradlew settings.gradle.kts build.gradle.kts gradle.properties ./
COPY gradle ./gradle
COPY backend/build.gradle.kts ./backend/build.gradle.kts
COPY backend/src ./backend/src
RUN --mount=type=cache,target=/root/.gradle \
    ./gradlew :backend:bootJar --no-daemon --console=plain

FROM eclipse-temurin:21-jre
WORKDIR /app
COPY --from=build /workspace/backend/build/libs/backend.jar ./backend.jar
COPY --chmod=755 docker/backend-service/start.sh ./start.sh
COPY --chmod=755 docker/backend-service/healthcheck.sh ./healthcheck.sh
CMD ["/app/start.sh"]
