// Copyright (c) 2026, Digital Asset (Switzerland) GmbH and/or its affiliates.
// SPDX-License-Identifier: 0BSD

package com.digitalasset.quickstart.ledger;

import com.digitalasset.quickstart.config.LedgerProperties;
import io.grpc.CallCredentials;
import io.grpc.ManagedChannel;
import io.grpc.Metadata;
import io.grpc.Status;
import io.grpc.netty.shaded.io.grpc.netty.NettyChannelBuilder;
import java.util.concurrent.Executor;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Profile;
import org.springframework.security.oauth2.client.AuthorizedClientServiceOAuth2AuthorizedClientManager;
import org.springframework.security.oauth2.client.OAuth2AuthorizeRequest;
import org.springframework.security.oauth2.client.OAuth2AuthorizedClientProviderBuilder;
import org.springframework.security.oauth2.client.OAuth2AuthorizedClientService;
import org.springframework.security.oauth2.client.registration.ClientRegistrationRepository;

@Configuration(proxyBeanMethods = false)
public class LedgerConfiguration {
    @Bean(destroyMethod = "shutdownNow")
    ManagedChannel ledgerChannel(LedgerProperties properties) {
        var builder = NettyChannelBuilder.forAddress(properties.host(), properties.port());
        if (properties.plaintext()) {
            builder.usePlaintext();
        }
        return builder.build();
    }

    @Bean
    @Profile("shared-secret")
    TokenProvider sharedSecretTokenProvider(LedgerProperties properties) {
        return properties::token;
    }

    @Bean
    @Profile("oauth2")
    TokenProvider oauth2TokenProvider(
            ClientRegistrationRepository registrations,
            OAuth2AuthorizedClientService clients) {
        var manager = new AuthorizedClientServiceOAuth2AuthorizedClientManager(registrations, clients);
        manager.setAuthorizedClientProvider(
                OAuth2AuthorizedClientProviderBuilder.builder().clientCredentials().build());
        return () -> {
            var request = OAuth2AuthorizeRequest.withClientRegistrationId("ledger")
                    .principal("backend-service").build();
            var client = manager.authorize(request);
            if (client == null) {
                throw new IllegalStateException("Ledger credentials are unavailable");
            }
            return client.getAccessToken().getTokenValue();
        };
    }

    @Bean
    CallCredentials ledgerCredentials(TokenProvider tokens) {
        return new CallCredentials() {
            @Override
            public void applyRequestMetadata(
                    RequestInfo request, Executor executor, MetadataApplier applier) {
                executor.execute(() -> {
                    try {
                        String token = tokens.getToken();
                        if (token == null || token.isBlank()) {
                            throw new IllegalStateException("Ledger token is missing");
                        }
                        var metadata = new Metadata();
                        metadata.put(Metadata.Key.of("Authorization", Metadata.ASCII_STRING_MARSHALLER),
                                "Bearer " + token);
                        applier.apply(metadata);
                    } catch (RuntimeException exception) {
                        applier.fail(Status.UNAUTHENTICATED
                                .withDescription("Ledger authentication failed")
                                .withCause(exception));
                    }
                });
            }
        };
    }
}
