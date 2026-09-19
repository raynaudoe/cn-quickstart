// Copyright (c) 2026, Digital Asset (Switzerland) GmbH and/or its affiliates.
// SPDX-License-Identifier: 0BSD
plugins {
    java
    id("org.springframework.boot") version "3.4.2"
}
repositories { mavenCentral() }
java {
    toolchain { languageVersion = JavaLanguageVersion.of(21) }
}
dependencies {
    implementation(platform("org.springframework.boot:spring-boot-dependencies:3.4.2"))
    implementation("org.springframework.boot:spring-boot-starter-web")
    implementation("org.springframework.boot:spring-boot-starter-jdbc")
    implementation("org.springframework.boot:spring-boot-starter-actuator")
    implementation("org.springframework.boot:spring-boot-starter-oauth2-client")
    implementation("org.springframework.boot:spring-boot-starter-oauth2-resource-server")
    implementation("io.grpc:grpc-netty-shaded:1.67.1")
    runtimeOnly("org.postgresql:postgresql:42.7.3")
}
tasks.bootJar { archiveFileName = "backend.jar" }
