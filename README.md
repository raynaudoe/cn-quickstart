# Canton application scaffold

A minimal application starting point built on
[Digital Asset CN Quickstart](https://github.com/digital-asset/cn-quickstart),
based on commit `8984e430bda8263dc726e70d157780767fe9b50d`.

The repository contains a browser shell, a Java 21 / Spring Boot backend,
Keycloak login, PostgreSQL, and Canton LocalNet. Business contracts, endpoints,
schemas, and DEX features have no implementation here.

## Run everything with Docker

Requirements: Docker with Compose 2.27+, Make, and at least 8 GB of memory
allocated to Docker. Docker builds both the backend and frontend; Java,
Gradle, and Node are not required on the host for this workflow.

From this directory:

```sh
make docker-run
```

The first run downloads images and dependencies and starts LocalNet. The
command waits for service health checks before printing the application URL.

Open **http://localhost:3001** and sign in with the local development account:

- Username: `developer`
- Password: `developer`

The browser shell supports sign-in, sign-out, and a connection check.
After sign-in, the check sends a JWT to the backend and checks the application
database. It does not submit Canton transactions.

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
| `http://localhost:3001/api/actuator/health` | Backend and PostgreSQL health |
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
| Startup | `quickstart/backend/src/main/java/com/digitalasset/quickstart/App.java` | Starts Spring Boot without business controllers. |
| HTTP security | `quickstart/backend/src/main/java/com/digitalasset/quickstart/security/SecurityConfiguration.java` | Stateless JWT authentication. Health is public. Other routes are denied in shared-secret mode. |
| Database | `quickstart/backend/src/main/resources/application.yml` | PostgreSQL JDBC driver, Hikari pool, and Spring JDBC against an empty `application` database. |
| Canton | `quickstart/backend/src/main/java/com/digitalasset/quickstart/ledger/LedgerConfiguration.java` | A managed gRPC channel, token provider, and per-call credentials. |
| Containers | `quickstart/compose.yaml`, `quickstart/backend/Dockerfile`, `quickstart/frontend/Dockerfile` | Image builds, private service networking, and readiness checks. |

Application users authenticate against the `Application` realm. The browser
uses the official [Keycloak JavaScript adapter](https://www.keycloak.org/securing-apps/javascript-adapter)
with Authorization Code and PKCE. Tokens stay in browser memory. The backend
validates the Application issuer and the `backend` audience.

The existing `AppProvider` and `AppUser` realms serve infrastructure identities.
Outbound backend-to-Canton authentication still uses the `app-provider-backend`
service account. Application login does not grant party rights.

Future Canton clients can inject `ManagedChannel` and `CallCredentials` and
attach credentials with `stub.withCallCredentials(credentials)`. There are no
generated contract bindings or Ledger API stubs yet. The backend's Ledger API
user starts without `actAs` or `readAs` rights; workflows must grant their
required authority explicitly.

External-wallet onboarding, external-party hosting, signing, application roles,
batching, and settlement remain application responsibilities. Wallet private
keys stay outside this scaffold.

## Development and checks

`make build` builds the backend locally and requires JDK 21.
`make check` additionally requires Python 3 and jq. It tests bootstrap error
handling and configuration validation, then checks shell syntax and all four
Compose combinations: both authentication modes, with PQS on and off. These
checks do not start LocalNet or exercise ledger operations.

The frontend Docker build runs the login and connection regression tests.
With Node 22 installed locally, run them with `npm --prefix quickstart/frontend test`.

`make canton-console` opens the participant console.
`make clean` removes local Gradle build outputs.

Health checks cover the backend process and PostgreSQL. Constructing the
Canton channel does not perform a Ledger API call, so backend health is not
evidence of ledger connectivity.

```text
quickstart/
  backend/              Spring Boot entry point, connection config, Dockerfile
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
