# Local identity configuration

Keycloak imports the JSON files in this directory when `AUTH_MODE=oauth2`.

`Application-realm.json` defines application login: the public `web` client
uses Authorization Code with PKCE, and the `developer` / `developer` account
is available for local development. Its redirect URL comes from
`APPLICATION_ORIGIN` when the realm is first imported.

The `AppProvider` and `AppUser` realms provide infrastructure identities for
validators, wallet and ANS interfaces, optional PQS, and the backend service
account. Application users do not inherit these identities or party rights.

These exports and the matching `env/` files contain local development
credentials. They are not deployment secrets.

[Startup import](https://www.keycloak.org/server/importExport) skips existing
realms. Change persisted clients and users through the admin console; restarting
does not overwrite them with the import files.
