// Copyright (c) 2026, Digital Asset (Switzerland) GmbH and/or its affiliates.
// SPDX-License-Identifier: 0BSD

package com.digitalasset.quickstart.ledger;

@FunctionalInterface
public interface TokenProvider {
    String getToken();
}
