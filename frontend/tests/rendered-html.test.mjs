import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

async function render() {
  const workerUrl = new URL("../dist/server/index.js", import.meta.url);
  workerUrl.searchParams.set("test", `${process.pid}-${Date.now()}`);
  const { default: worker } = await import(workerUrl.href);

  return worker.fetch(
    new Request("http://localhost/", {
      headers: { accept: "text/html" },
    }),
    {
      ASSETS: {
        fetch: async () => new Response("Not found", { status: 404 }),
      },
    },
    {
      waitUntil() {},
      passThroughOnException() {},
    },
  );
}

test("server-renders the TenantBill sign-in experience", async () => {
  const response = await render();
  assert.equal(response.status, 200);
  assert.match(response.headers.get("content-type") ?? "", /^text\/html\b/i);

  const html = await response.text();
  assert.match(html, /<html lang="en">/i);
  assert.match(html, /<title>TenantBill — Billing operations<\/title>/i);
  assert.match(html, /Recurring revenue,/);
  assert.match(html, /without blind spots\./);
  assert.match(html, /Welcome back/);
  assert.match(html, /demo@tenantbill\.local/);
  assert.match(html, /Open dashboard/);
  assert.doesNotMatch(html, /Bem-vindo|Visão geral|Entrar no dashboard/);
});

test("keeps the dashboard contract aligned with the Django API", async () => {
  const [page, layout] = await Promise.all([
    readFile(new URL("../app/page.tsx", import.meta.url), "utf8"),
    readFile(new URL("../app/layout.tsx", import.meta.url), "utf8"),
  ]);

  for (const endpoint of [
    "/api/auth/login/",
    "/api/tenants/me/",
    "/api/subscriptions/",
    "/api/usage/",
    "/api/invoices/",
    "/api/usage/events/",
  ]) {
    assert.ok(page.includes(endpoint), `missing API contract for ${endpoint}`);
  }

  assert.match(page, /"X-Tenant-Slug": "acme-demo"/);
  assert.match(page, /idempotency_key: `portfolio-\$\{Date\.now\(\)\}`/);
  assert.match(page, /localStorage\.setItem\("tenantbill_access", data\.access\)/);
  assert.match(page, /new Intl\.NumberFormat\("en-US"/);
  assert.match(layout, /description: "Demo dashboard for recurring and usage-based SaaS billing\."/);
  assert.match(layout, /<html lang="en">/);
});
