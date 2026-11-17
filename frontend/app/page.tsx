"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type Tenant = { id: number; name: string; slug: string };
type Subscription = {
  id: number;
  customer_name: string;
  status: string;
  current_period_start: string;
  current_period_end: string;
  plan: { name: string; price_cents: number; currency: string; included_usage_units: number };
};
type Usage = {
  subscription_id: number;
  included_units: number;
  total_quantity: number;
  metrics: { metric_id: number; metric_code: string; quantity: number }[];
};
type Invoice = {
  id: number;
  number: string;
  status: string;
  total_cents: number;
  currency: string;
  created_at: string;
  pdf_url: string | null;
};

function money(cents: number, currency = "USD") {
  return new Intl.NumberFormat("en-US", { style: "currency", currency }).format(cents / 100);
}

function number(value: number) {
  return new Intl.NumberFormat("en-US").format(value);
}

export default function Home() {
  const [token, setToken] = useState("");
  const [tenant, setTenant] = useState<Tenant | null>(null);
  const [subscription, setSubscription] = useState<Subscription | null>(null);
  const [usage, setUsage] = useState<Usage | null>(null);
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [email, setEmail] = useState("demo@tenantbill.local");
  const [password, setPassword] = useState("demo-password");
  const [quantity, setQuantity] = useState("250");
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");

  const authHeaders = useMemo(
    () => ({ Authorization: `Bearer ${token}`, "X-Tenant-Slug": "acme-demo" }),
    [token],
  );

  async function loadDashboard(accessToken: string) {
    const headers = { Authorization: `Bearer ${accessToken}`, "X-Tenant-Slug": "acme-demo" };
    const [tenantResponse, subscriptionResponse, usageResponse, invoiceResponse] = await Promise.all([
      fetch(`${API_URL}/api/tenants/me/`, { headers }),
      fetch(`${API_URL}/api/subscriptions/`, { headers }),
      fetch(`${API_URL}/api/usage/`, { headers }),
      fetch(`${API_URL}/api/invoices/`, { headers }),
    ]);
    if ([tenantResponse, subscriptionResponse, usageResponse, invoiceResponse].some((r) => !r.ok)) {
      throw new Error("Unable to load tenant data.");
    }
    const subscriptions = (await subscriptionResponse.json()) as Subscription[];
    const usages = (await usageResponse.json()) as Usage[];
    setTenant(await tenantResponse.json());
    setSubscription(subscriptions[0] ?? null);
    setUsage(usages[0] ?? null);
    setInvoices(await invoiceResponse.json());
  }

  useEffect(() => {
    const saved = window.localStorage.getItem("tenantbill_access");
    if (!saved) return;
    Promise.resolve().then(() => {
      setToken(saved);
      return loadDashboard(saved);
    }).catch(() => window.localStorage.removeItem("tenantbill_access"));
  }, []);

  async function login(event: FormEvent) {
    event.preventDefault();
    setLoading(true);
    setMessage("");
    try {
      const response = await fetch(`${API_URL}/api/auth/login/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username: email, password }),
      });
      if (!response.ok) throw new Error("Invalid email or password.");
      const data = await response.json();
      setToken(data.access);
      window.localStorage.setItem("tenantbill_access", data.access);
      await loadDashboard(data.access);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Unable to sign in.");
    } finally {
      setLoading(false);
    }
  }

  async function addUsage(event: FormEvent) {
    event.preventDefault();
    if (!subscription || !usage?.metrics[0]) return;
    setLoading(true);
    setMessage("");
    try {
      const response = await fetch(`${API_URL}/api/usage/events/`, {
        method: "POST",
        headers: { ...authHeaders, "Content-Type": "application/json" },
        body: JSON.stringify({
          subscription_id: subscription.id,
          metric_id: usage.metrics[0].metric_id,
          quantity: Number(quantity),
          idempotency_key: `portfolio-${Date.now()}`,
          metadata: { source: "portfolio-dashboard" },
        }),
      });
      if (!response.ok) throw new Error("Unable to record usage.");
      await loadDashboard(token);
      setMessage(`${number(Number(quantity))} units recorded successfully.`);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Unable to record usage.");
    } finally {
      setLoading(false);
    }
  }

  function logout() {
    window.localStorage.removeItem("tenantbill_access");
    setToken("");
    setTenant(null);
  }

  if (!tenant) {
    return (
      <main className="login-shell">
        <section className="login-story">
          <a className="brand light" href="#">TenantBill<span>.</span></a>
          <div>
            <p className="eyebrow light">Billing infrastructure</p>
            <h1>Recurring revenue,<br />without blind spots.</h1>
            <p className="story-copy">Reliable infrastructure for subscriptions, usage, and multi-tenant financial operations.</p>
          </div>
          <p className="story-foot">Django · PostgreSQL · Stripe · Celery</p>
        </section>
        <section className="login-panel">
          <form className="login-card" onSubmit={login}>
            <p className="eyebrow">Demo environment</p>
            <h2>Welcome back</h2>
            <p className="muted">Access the Acme Demo workspace.</p>
            <label>Email<input value={email} onChange={(e) => setEmail(e.target.value)} type="email" required /></label>
            <label>Password<input value={password} onChange={(e) => setPassword(e.target.value)} type="password" required /></label>
            {message && <p className="feedback error">{message}</p>}
            <button className="primary" disabled={loading}>{loading ? "Signing in…" : "Open dashboard"}</button>
            <p className="demo-hint">Demo credentials are pre-filled</p>
          </form>
        </section>
      </main>
    );
  }

  const percent = usage ? Math.min((usage.total_quantity / usage.included_units) * 100, 100) : 0;
  return (
    <main className="app-shell">
      <aside>
        <a className="brand" href="#">TenantBill<span>.</span></a>
        <nav>
          <a className="active" href="#overview"><i>01</i>Overview</a>
          <a href="#usage"><i>02</i>Usage</a>
          <a href="#invoices"><i>03</i>Invoices</a>
        </nav>
        <div className="aside-bottom">
          <div className="tenant-mini"><b>AD</b><span><strong>{tenant.name}</strong><small>Owner workspace</small></span></div>
          <button className="text-button" onClick={logout}>Sign out</button>
        </div>
      </aside>
      <section className="content">
        <header>
          <div><p className="eyebrow">Workspace / {tenant.slug}</p><h1>Overview</h1></div>
          <span className="live"><i /> All systems operational</span>
        </header>

        <section id="overview" className="hero-grid">
          <article className="plan-card">
            <div className="card-top"><span>Current plan</span><em>{subscription?.status ?? "—"}</em></div>
            <h2>{subscription?.plan.name ?? "No active subscription"}</h2>
            <p><strong>{subscription ? money(subscription.plan.price_cents, subscription.plan.currency) : "—"}</strong> / month</p>
            <div className="plan-meta"><span>Next renewal</span><b>{subscription ? new Date(`${subscription.current_period_end}T12:00:00`).toLocaleDateString("en-US") : "—"}</b></div>
          </article>
          <article className="metric-card"><span>Usage this period</span><strong>{number(usage?.total_quantity ?? 0)}</strong><small>of {number(usage?.included_units ?? 0)} included units</small><div className="progress"><i style={{ width: `${percent}%` }} /></div><p>{percent.toFixed(1)}% used</p></article>
          <article className="metric-card"><span>Invoices</span><strong>{invoices.length}</strong><small>financial documents</small><div className="invoice-total">{invoices[0] ? money(invoices[0].total_cents, invoices[0].currency) : "—"}<span>latest charge</span></div></article>
        </section>

        <section id="usage" className="section-block">
          <div className="section-heading"><div><p className="eyebrow">Usage-based billing</p><h2>Record usage</h2></div><p>Simulate an idempotent usage event for the active subscription.</p></div>
          <form className="usage-form" onSubmit={addUsage}>
            <label>Request quantity<input min="1" value={quantity} onChange={(e) => setQuantity(e.target.value)} type="number" required /></label>
            <div><span>Metric</span><strong>{usage?.metrics[0]?.metric_code ?? "api-requests"}</strong></div>
            <div><span>Subscription</span><strong>#{subscription?.id}</strong></div>
            <button className="primary" disabled={loading}>{loading ? "Recording…" : "Record event"}</button>
          </form>
          {message && <p className="feedback">{message}</p>}
        </section>

        <section id="invoices" className="section-block">
          <div className="section-heading"><div><p className="eyebrow">Financial history</p><h2>Recent invoices</h2></div></div>
          <div className="table-wrap"><table><thead><tr><th>Invoice</th><th>Issued</th><th>Status</th><th>Total</th><th /></tr></thead><tbody>{invoices.map((invoice) => <tr key={invoice.id}><td><strong>{invoice.number || `#${invoice.id}`}</strong></td><td>{new Date(invoice.created_at).toLocaleDateString("en-US")}</td><td><span className="status">{invoice.status}</span></td><td><strong>{money(invoice.total_cents, invoice.currency)}</strong></td><td>{invoice.pdf_url ? <a className="download" href={invoice.pdf_url}>Download PDF</a> : <span className="muted">PDF pending</span>}</td></tr>)}</tbody></table></div>
        </section>
      </section>
    </main>
  );
}
