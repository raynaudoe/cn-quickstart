// Copyright (c) 2026, Digital Asset (Switzerland) GmbH and/or its affiliates.
// SPDX-License-Identifier: 0BSD

// Bare backend template. It answers each request with an empty 404 until the application adds routes.
import { createServer } from 'node:http';

const DEFAULT_PORT = 8080;

function listenPort(): number {
  const raw = process.env['BACKEND_PORT'];
  if (raw === undefined || raw === '') return DEFAULT_PORT;
  const value = Number(raw);
  if (!/^\d+$/.test(raw) || value < 1 || value > 65_535) {
    throw new Error('Invalid configuration: BACKEND_PORT must be a TCP port');
  }
  return value;
}

const port = listenPort();
const server = createServer((_request, response) => {
  response.statusCode = 404;
  response.end();
});

for (const signal of ['SIGTERM', 'SIGINT'] as const) {
  process.once(signal, () => {
    console.info(`${signal} received; stopping`);
    server.close(() => process.exit(0));
  });
}

server.listen(port, '0.0.0.0', () => console.info(`Listening on ${port}`));
