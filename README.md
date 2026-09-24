# Canton application scaffold

A minimal application starting point built on
[Digital Asset CN Quickstart](https://github.com/digital-asset/cn-quickstart),
based on commit `8984e430bda8263dc726e70d157780767fe9b50d`.

The repository contains a browser shell, a bare Node.js 24 / TypeScript backend,
Keycloak login, PostgreSQL, and Canton LocalNet. Business contracts, endpoints,
schemas, and DEX features have no implementation here.
TypeScript is the default backend setup; you can replace it with any language or runtime.

## Run everything with Docker

Requirements: Docker with Compose 2.27+, Make, and at least 8 GB of memory
allocated to Docker. Docker builds both the backend and frontend; Node is not
required on the host for this workflow.

From this directory:

```sh
make docker-run
```

The first run downloads images and dependencies and starts LocalNet. The
command waits for service health checks before printing the application URL.

Open **http://localhost:3001** and sign in with the local development account:

- Username: `developer`
- Password: `developer`

The existing browser shell and local login are preserved. Its connection check
calls `/api/actuator/health`, which the empty backend does not implement and
returns 404. Add application endpoints when building your backend.

```sh
make status
make logs
make docker-stop
```

Stopping preserves database volumes and users. Running `make docker-run` again
rebuilds changed application code and reuses the stored data. `make start`
and `make stop` are aliases for the Docker workflow.

## Configuration

`make setup` creates `quickstart/.env.local` if it does not exist. Example:

```dotenv
AUTH_MODE=oauth2
PQS_ENABLED=false
FRONTEND_PORT=3001
```

`AUTH_MODE=oauth2` enables Keycloak and application login.
`AUTH_MODE=shared-secret` starts LocalNet without Keycloak; the browser shell
then exposes only its public connection check.
`PQS_ENABLED=true` adds an AppProvider ledger projection. The application
database and backend startup do not depend on PQS.

All files selected by `quickstart/Makefile` are merged into one Compose project.
`make compose-config` prints the full resolved configuration.

| Local URL | Service |
| --- | --- |
| `http://localhost:3001` | Application browser shell |
| `http://keycloak.localhost:8082` | Keycloak; admin console uses `admin` / `admin` locally |
| `http://wallet.localhost:3000` | Local AppProvider infrastructure wallet |
| `http://scan.localhost:4000` | Local Scan |

The browser proxies `/api/` to the backend over the Docker network. The backend
port is internal, so the application does not bind host port 8080.
Infrastructure ports and container names retain the upstream defaults; run one
instance at a time. This environment uses local development credentials and
HTTP, not production deployment settings.

Keycloak imports the `Application` realm and its browser redirect URL on first
startup. Existing realms are preserved on subsequent runs. If changing
`FRONTEND_PORT` after the first run, also update the `web` client's redirect
URIs and web origins in that realm. Changes to import files do not overwrite
existing users or client configuration.

## Application wiring

| Area | Entry point | Current behavior |
| --- | --- | --- |
| Browser | `quickstart/frontend/src/app.js` | Minimal login and connection screen, served by Nginx. |
| Backend | `quickstart/backend/src/main.ts` | An HTTP listener with no routes or application logic. All requests return an empty 404. SIGTERM stops it gracefully. |
| Database | `quickstart/compose.yaml` | An empty `application` database and `POSTGRES_*` configuration are available. The backend has no database driver or queries. |
| Containers | `quickstart/compose.yaml`, `quickstart/backend/Dockerfile`, `quickstart/frontend/Dockerfile` | Image builds, private service networking, and readiness checks. |

Application users authenticate against the `Application` realm. The browser
uses the official [Keycloak JavaScript adapter](https://www.keycloak.org/securing-apps/javascript-adapter)
with Authorization Code and PKCE. Tokens stay in browser memory. The bare
backend does not validate them; an application adds validation of the
Application issuer and the `backend` audience.

The existing `AppProvider` and `AppUser` realms serve infrastructure identities.
LocalNet onboarding creates the Ledger API user of the `app-provider-backend`
service account. Application login does not grant party rights.

The participants serve the JSON Ledger API v2, which an application backend can
call over HTTP with the service-account token. There are no generated contract
bindings or Ledger API clients yet. The backend's Ledger API user starts without
`actAs` or `readAs` rights; workflows must grant their required authority
explicitly.

External-wallet onboarding, external-party hosting, signing, application roles,
batching, and settlement remain application responsibilities. Wallet private
keys stay outside this scaffold.

## Development and checks

`make build` builds the backend locally and requires Node 24.
`make check` additionally requires Python 3 and jq. It tests bootstrap error
handling and configuration validation, then checks shell syntax and all four
Compose combinations: both authentication modes, with PQS on and off. These
checks do not start LocalNet or exercise ledger operations.

The frontend Docker build runs the login and connection regression tests.
With Node 22 installed locally, run them with `npm --prefix quickstart/frontend test`.

`make canton-console` opens the participant console.
`make clean` removes the local backend build output.

The backend container health check only verifies its TCP listener. PostgreSQL
has its own infrastructure health check. The backend has no database or ledger
connection and no runtime package dependencies.

To develop the backend locally:

```sh
cd quickstart/backend
npm ci
npm run dev
```

It listens on port 8080 by default; set `BACKEND_PORT` to override it.

```text
quickstart/
  backend/              Empty HTTP listener, TypeScript configuration, Dockerfile
  frontend/             Browser shell, login adapter, reverse proxy, Dockerfile
  docker/backend-service/
                        Backend startup, health, Ledger API identity provisioning
  docker/modules/
    localnet/           Canton, Splice, PostgreSQL, infrastructure UIs
    splice-onboarding/  Local node initialization and optional DAR upload hook
    keycloak/           Application login and infrastructure identities
    pqs/                Optional ledger projection
  scripts/              Scaffold configuration checks
  compose.yaml
  Makefile
```

The application has no Daml build, DAR artifacts, OpenAPI code generation, or
sample domain dependencies. Infrastructure versions remain pinned to the
upstream baseline. See `LICENSE`, `terms.md`, and source-file license headers.

## Shared infrastructure releases

The [LocalNet infrastructure bundle](infra/README.md) lets applications consume
versioned Compose configuration without cloning this repository.
