"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { AdminGuard } from "@/components/admin/AdminGuard";
import { Card, PageShell } from "@/components/ui";
import { adminApi } from "@/lib/api";
import { getToken } from "@/lib/auth";
import type { AdminAnalytics, AdminMetrics } from "@/types/api";

const metricLabels: { key: keyof AdminMetrics; label: string }[] = [
  { key: "total_applications", label: "Total Applications" },
  { key: "gst_applications", label: "GST Applications" },
  { key: "fssai_applications", label: "FSSAI Applications" },
  { key: "udyam_applications", label: "Udyam Applications" },
  { key: "documents_pending", label: "Documents Pending" },
  { key: "under_review", label: "Under Review" },
  { key: "clarification_required", label: "Clarification Required" },
  { key: "approved", label: "Approved" },
  { key: "rejected", label: "Rejected" },
];

export default function AdminDashboardPage() {
  const [metrics, setMetrics] = useState<AdminMetrics | null>(null);
  const [analytics, setAnalytics] = useState<AdminAnalytics | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    const token = getToken();
    if (!token) return;
    adminApi.metrics(token).then(setMetrics).catch((err) => {
      setError(err instanceof Error ? err.message : "Could not load metrics");
    });
    adminApi.analytics(token).then(setAnalytics).catch(() => undefined);
  }, []);

  return (
    <AdminGuard>
      <PageShell>
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="text-3xl font-bold text-ink">Admin dashboard</h1>
            <p className="mt-2 text-sm text-slate-600">Review customer applications and document status.</p>
          </div>
          <Link href="/admin/applications" className="rounded-md bg-saffron px-4 py-2 text-sm font-semibold text-white">
            Open applications
          </Link>
          <Link href="/admin/leads" className="rounded-md border border-slate-300 px-4 py-2 text-sm font-semibold">
            Leads
          </Link>
          <Link href="/admin/notifications" className="rounded-md border border-slate-300 px-4 py-2 text-sm font-semibold">
            Notifications
          </Link>
        </div>

        {error ? <p className="mt-6 rounded-md bg-red-50 p-3 text-sm text-red-700">{error}</p> : null}

        <section className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {metricLabels.map((metric) => (
            <Card key={metric.key}>
              <p className="text-sm font-medium text-slate-600">{metric.label}</p>
              <p className="mt-2 text-3xl font-bold text-ink">{metrics ? metrics[metric.key] : "..."}</p>
            </Card>
          ))}
        </section>
        <section className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <Card>
            <p className="text-sm font-medium text-slate-600">Leads</p>
            <p className="mt-2 text-3xl font-bold text-ink">{analytics ? analytics.leads : "..."}</p>
          </Card>
          <Card>
            <p className="text-sm font-medium text-slate-600">Conversion rate</p>
            <p className="mt-2 text-3xl font-bold text-ink">
              {analytics ? `${analytics.conversion_rate}%` : "..."}
            </p>
          </Card>
          <Card>
            <p className="text-sm font-medium text-slate-600">Revenue placeholder</p>
            <p className="mt-2 text-lg font-bold text-ink">
              {analytics ? analytics.revenue_placeholder : "..."}
            </p>
          </Card>
        </section>
      </PageShell>
    </AdminGuard>
  );
}
