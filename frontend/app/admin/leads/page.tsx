"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { AdminGuard } from "@/components/admin/AdminGuard";
import { Card, PageShell } from "@/components/ui";
import { adminApi } from "@/lib/api";
import { getToken } from "@/lib/auth";
import type { Lead } from "@/types/api";

export default function AdminLeadsPage() {
  const [leads, setLeads] = useState<Lead[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    const token = getToken();
    if (!token) return;
    adminApi.leads(token).then(setLeads).catch((err) => {
      setError(err instanceof Error ? err.message : "Could not load leads");
    });
  }, []);

  return (
    <AdminGuard>
      <PageShell>
        <div>
          <h1 className="text-3xl font-bold text-ink">Leads</h1>
          <p className="mt-2 text-sm text-slate-600">Manage incoming enquiries from the landing page.</p>
        </div>
        {error ? <p className="mt-6 rounded-md bg-red-50 p-3 text-sm text-red-700">{error}</p> : null}
        <Card className="mt-6 overflow-x-auto">
          <table className="w-full min-w-[720px] text-left text-sm">
            <thead className="border-b border-slate-200 text-xs uppercase text-slate-500">
              <tr>
                <th className="py-3 pr-3">Name</th>
                <th className="py-3 pr-3">Mobile</th>
                <th className="py-3 pr-3">Service</th>
                <th className="py-3 pr-3">Status</th>
                <th className="py-3 pr-3">Created</th>
              </tr>
            </thead>
            <tbody>
              {leads.map((lead) => (
                <tr key={lead.id} className="border-b border-slate-100">
                  <td className="py-3 pr-3">
                    <Link href={`/admin/leads/${lead.id}`} className="font-semibold text-saffron">
                      {lead.name}
                    </Link>
                  </td>
                  <td className="py-3 pr-3">{lead.mobile}</td>
                  <td className="py-3 pr-3">{lead.service_interest.replaceAll("_", " ")}</td>
                  <td className="py-3 pr-3">{lead.status}</td>
                  <td className="py-3 pr-3">{new Date(lead.created_at).toLocaleDateString("en-IN")}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {leads.length === 0 ? <p className="py-4 text-sm text-slate-600">No leads yet.</p> : null}
        </Card>
      </PageShell>
    </AdminGuard>
  );
}
