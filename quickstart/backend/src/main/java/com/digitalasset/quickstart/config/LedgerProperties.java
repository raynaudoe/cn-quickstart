// Copyright (c) 2026, Digital Asset (Switzerland) GmbH and/or its affiliates.
// SPDX-License-Identifier: 0BSD

package com.digitalasset.quickstart.config;

import org.springframework.boot.context.properties.ConfigurationProperties;

@ConfigurationProperties("ledger")
public record LedgerProperties(String host, int port, boolean plaintext, String token) {}
