# Shared LocalNet infrastructure

`compose.yaml` runs PostgreSQL, Keycloak, Canton, Splice, and a separate application
participant for a consuming application's development environment. The configuration
uses public development credentials. It is intended for local development.

The Canton and Splice services use INFO logging with three rotated 50 MB log files.
The SV configuration pauses `ReconcileSequencingParametersTrigger` to avoid the
LocalNet busy loop in the pinned Splice version.

## Release bundle

The `cn-localnet-vX.Y.Z.tar.gz` release asset contains `infra/`, every file mounted
from `quickstart/docker/modules/`, `LICENSE`, `terms.md`, and `manifest.json`.
Relative paths are preserved so applications can include `infra/compose.yaml`
directly after extracting the archive. The manifest records the source commit,
image references, and each file's checksum and permissions.

Docker pulls the images listed in the manifest from their existing registries.
The bundle contains no container images, database volumes, application code, or
developer-specific environment overrides.

## Build a release

From the repository root, with Git, Python 3.12+, and Docker Compose installed:

```sh
make package-localnet VERSION=v0.1.0
```

The packager reads committed files at `HEAD`, discovers the Compose bind mounts,
and validates that the extracted bundle resolves to the same Compose configuration.
It writes the archive, a standalone manifest, and `SHA256SUMS` into `.release/`.
Identical source commits and versions produce identical archives. Packaging does
not start containers or test ledger behavior.

Publish those three files under a `localnet-vX.Y.Z` GitHub release whose tag points
to the manifest's source commit. Consumers pin the asset URL and archive SHA-256
in their own repository. A release upgrade is an explicit dependency update.
