import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { setImmediate } from "node:timers/promises";
import test from "node:test";
import { runInNewContext } from "node:vm";

const html = readFileSync(new URL("../public/index.html", import.meta.url), "utf8");
// Replace only the identity-service import; execute the actual application startup.
const source = readFileSync(new URL("../src/app.js", import.meta.url), "utf8")
  .replace(/^import Keycloak from "keycloak-js";\n/, "");

async function openPage(options = {}) {
  const elements = new Map();
  for (const [tag, id] of html.matchAll(/<[^>]+\bid="([^"]+)"[^>]*>/g)) {
    elements.set(id, {
      textContent: "", hidden: /\bhidden\b/.test(tag), disabled: /\bdisabled\b/.test(tag),
      listeners: new Map(),
      addEventListener(event, callback) { this.listeners.set(event, callback); },
    });
  }
  const element = (id) => {
    assert.ok(elements.has(id), `Unknown element: ${id}`);
    return elements.get(id);
  };
  const identity = {
    authenticated: options.authenticated ?? true,
    token: "test-access-token",
    tokenParsed: { preferred_username: "developer" },
    async init() { if ("initError" in options) throw options.initError; },
    async updateToken() {},
    async login() {},
    async logout() {},
    clearToken() {
      this.authenticated = false;
      this.token = undefined;
      this.tokenParsed = undefined;
      this.onAuthLogout?.();
    },
  };
  const requests = [];
  const api = { status: 200 };
  runInNewContext(source, {
    window: { APP_CONFIG: { authMode: "oauth2" }, location: { origin: "http://localhost" } },
    document: { getElementById: element },
    Keycloak: class { constructor() { return identity; } },
    fetch: async (url, request) => {
      requests.push({ url, ...request });
      return { ok: api.status === 200, status: api.status, json: async () => ({ status: "UP" }) };
    },
  });
  await setImmediate();
  return { element, identity, requests, api, click: (id) => element(id).listeners.get("click")() };
}

test("an authenticated health check sends the access token", async () => {
  const page = await openPage();
  assert.equal(page.requests[0].headers.Authorization, "Bearer test-access-token");
  assert.equal(page.element("session").textContent, "Welcome, developer.");
  assert.equal(page.element("connection").textContent, "Connected");
});

test("API checks preserve an initialization error in the session panel", async () => {
  const page = await openPage({ authenticated: false, initError: new Error("Realm unavailable") });
  await page.click("refresh");
  assert.equal(page.element("session-error").textContent, "Realm unavailable");
  assert.equal(page.element("session-error").hidden, false);
  assert.equal(page.element("connection-error").hidden, true);
  assert.equal(page.element("connection").textContent, "Connected");
});

test("expired refresh tokens restore sign-in and preserve the session error", async () => {
  const page = await openPage();
  page.identity.updateToken = async () => {
    page.identity.clearToken();
    throw "Session expired";
  };
  await page.click("refresh");
  assert.equal(page.element("login").hidden, false);
  assert.equal(page.element("login").disabled, false);
  assert.equal(page.element("logout").hidden, true);
  assert.equal(page.element("session").textContent, "Ready when you are.");
  assert.equal(page.element("refresh").disabled, false);
  await page.click("refresh");
  assert.equal(page.requests.at(-1).headers.Authorization, undefined);
  assert.equal(page.element("connection").textContent, "Connected");
  assert.equal(page.element("session-error").textContent, "Session expired");
  assert.equal(page.element("session-error").hidden, false);
});

for (const [reason, expected] of [
  [undefined, "The request failed. Please try again."],
  ["Refresh service unavailable", "Refresh service unavailable"],
  [new Error("Refresh rejected"), "Refresh rejected"],
]) {
  test(`refresh rejection is safe: ${expected}`, async () => {
    const page = await openPage();
    page.identity.updateToken = async () => { throw reason; };
    await page.click("refresh");
    assert.equal(page.element("session-error").textContent, expected);
    assert.equal(page.element("session-error").hidden, false);
    assert.equal(page.element("refresh").disabled, false);
    assert.equal(page.element("login").hidden, true);
    assert.equal(page.requests.length, 1);
    page.identity.updateToken = async () => {};
    await page.click("refresh");
    assert.equal(page.element("session-error").hidden, true);
    assert.equal(page.element("connection").textContent, "Connected");
  });
}

test("an API failure belongs to the connection panel and recovers", async () => {
  const page = await openPage();
  page.api.status = 503;
  await page.click("refresh");
  assert.match(page.element("connection-error").textContent, /503/);
  assert.equal(page.element("connection-error").hidden, false);
  assert.equal(page.element("session-error").hidden, true);
  assert.equal(page.element("session").textContent, "Welcome, developer.");
  page.api.status = 200;
  await page.click("refresh");
  assert.equal(page.element("connection-error").hidden, true);
});
