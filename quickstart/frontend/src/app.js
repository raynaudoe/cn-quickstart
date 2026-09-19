import Keycloak from "keycloak-js";

const element = (id) => document.getElementById(id);
const config = window.APP_CONFIG;
let identity;

function showError(id, error) {
  const message = typeof error === "string" ? error : error?.message;
  element(id).textContent = message || "The request failed. Please try again.";
  element(id).hidden = false;
}

function renderSession() {
  const signedIn = Boolean(identity.authenticated);
  element("login").hidden = signedIn;
  element("logout").hidden = !signedIn;
  element("login").disabled = false;
  element("session").textContent = signedIn
    ? `Welcome, ${identity.tokenParsed.preferred_username || "you"}.`
    : "Ready when you are.";
  element("session-detail").textContent = signedIn
    ? "You are signed in to your local workspace."
    : "Sign in to connect your account to the workspace.";
}

async function checkConnection() {
  element("refresh").disabled = true;
  element("connection-error").hidden = true;
  try {
    const headers = {};
    if (identity?.authenticated) {
      try {
        await identity.updateToken(30);
      } catch (error) {
        showError("session-error", error);
        element("connection").textContent = "Connection not checked";
        element("connection-detail").textContent = "Resolve the session error, then try again.";
        return;
      }
      element("session-error").hidden = true;
      headers.Authorization = `Bearer ${identity.token}`;
    }
    const response = await fetch("/api/actuator/health", { headers, cache: "no-store" });
    if (!response.ok) throw new Error(`Connection check failed (HTTP ${response.status}).`);
    const health = await response.json();
    if (health.status !== "UP") throw new Error("The workspace is still starting.");
    element("connection").textContent = "Connected";
    element("connection-detail").textContent = identity?.authenticated
      ? "Your session is accepted by the API. The application database is available."
      : "The API and application database are available.";
  } catch (error) {
    element("connection").textContent = "Connection unavailable";
    element("connection-detail").textContent = "Check that the local environment is running, then try again.";
    showError("connection-error", error);
  } finally {
    element("refresh").disabled = false;
  }
}

async function initialize() {
  element("refresh").addEventListener("click", checkConnection);
  if (config.authMode !== "oauth2") {
    element("session").textContent = "Local mode";
    element("session-detail").textContent = "Sign-in is unavailable in this environment.";
    element("login").hidden = true;
    await checkConnection();
    return;
  }
  identity = new Keycloak({ url: config.authUrl, realm: config.realm, clientId: config.clientId });
  identity.onAuthLogout = renderSession;
  try {
    await identity.init({ onLoad: "check-sso", pkceMethod: "S256", checkLoginIframe: false });
    renderSession();
    element("login").addEventListener("click", () =>
      identity.login().catch((error) => showError("session-error", error)));
    element("logout").addEventListener("click", () =>
      identity.logout({ redirectUri: window.location.origin + "/" })
        .catch((error) => showError("session-error", error)));
  } catch (error) {
    element("session").textContent = "Sign-in unavailable";
    element("session-detail").textContent = "Reload once the identity service is available.";
    showError("session-error", error);
  }
  await checkConnection();
}

initialize().catch((error) => showError("session-error", error));
