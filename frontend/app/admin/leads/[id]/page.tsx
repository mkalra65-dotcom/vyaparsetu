"use client";

import { useParams } from "next/navigation";
import { FormEvent, useEffect, useState } from "react";
import { AdminGuard } from "@/components/admin/AdminGuard";
import { Card, Field, PageShell, inputClass } from "@/components/ui";
import { adminApi } from "@/lib/api";
import { getToken } from "@/lib/auth";
import type { Lead, LeadStatus } from "@/types/api";

const statuses: LeadStatus[] = ["new", "contacted", "qualified", "converted", "lost"];

export default function AdminLeadDetailPage() {
  const params = useParams<{ id: string }>();
  const [lead, setLead] = useState<Lead | null>(null);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    const token = getToken();
    if (!token) return;
    adminApi.lead(token, params.id).then(setLead).catch((err) => {
      setError(err instanceof Error ? err.message : "Could not load lead");
    });
  }, [params.id]);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const token = getToken();
    if (!token) return;
    const form = new FormData(event.currentTarget);
    try {
      const updated = await adminApi.updateLeadStatus(token, params.id, String(form.get("status")) as LeadStatus);
      setLead(updated);
      setMessage("Lead status updated");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not update lead");
    }
  }

  return (
    <AdminGuard>
      <PageShell>
        {!lead ? (
          <p className="text-sm text-slate-600">{error || "Loading lead..."}</p>
        ) : (
          <div className="grid gap-6 lg:grid-cols-[1fr_0.8fr]">
            <Card>
              <h1 className="text-3xl font-bold text-ink">{lead.name}</h1>
              <div className="mt-5 grid gap-3 text-sm text-slate-700">
                <p>Mobile: {lead.mobile}</p>
                <p>Email: {lead.email || "Not provided"}</p>
                <p>Service: {lead.service_interest.replaceAll("_", " ")}</p>
                <p>Status: {lead.status}</p>
                <p>Message: {lead.message || "No message"}</p>
              </div>
            </Card>
            <Card>
              <h2 className="text-xl font-bold text-ink">Lead status</h2>
              <form onSubmit={onSubmit} className="mt-4 grid gap-4">
                <Field label="Status">
                  <select name="status" defaultValue={lead.status} className={inputClass}>
                    {statuses.map((status) => (
                      <option key={status} value={status}>
                        {status}
                      </option>
                    ))}
                  </select>
                </Field>
                {message ? <p className="text-sm text-green-700">{message}</p> : null}
                {error ? <p className="text-sm text-red-700">{error}</p> : null}
                <button className="min-h-11 rounded-md bg-ink px-4 py-2 text-sm font-semibold text-white">
                  Update status
                </button>
              </form>
            </Card>
          </div>
        )}
      </PageShell>
    </AdminGuard>
  );
}
