"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";
import { AdminGuard } from "@/components/admin/AdminGuard";
import { Card, Field, PageShell, inputClass } from "@/components/ui";
import { adminApi } from "@/lib/api";
import { getToken } from "@/lib/auth";
import type { AdminApplicationFilters, Application } from "@/types/api";

const serviceLabels: Record<string, string> = {
  gst_registration: "GST",
  fssai_registration: "FSSAI",
  udyam_registration: "Udyam",
};

const statuses = [
  "documents_pending",
  "under_review",
  "clarification_required",
  "approved",
  "rejected",
];

function startOfDay(value: string): string | undefined {
  return value ? `${value}T00:00:00` : undefined;
}

function endOfDay(value: string): string | undefined {
  return value ? `${value}T23:59:59` : undefined;
}

export default function AdminApplicationsPage() {
  const [applications, setApplications] = useState<Application[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [filters, setFilters] = useState<AdminApplicationFilters>({ page: 1, page_size: 10 });
  const [error, setError] = useState("");

  async function load(nextFilters: AdminApplicationFilters) {
    const token = getToken();
    if (!token) return;
    const response = await adminApi.listApplications(token, nextFilters);
    setApplications(response.items);
    setTotal(response.total);
    setPage(response.page);
  }

  useEffect(() => {
    load(filters).catch((err) => setError(err instanceof Error ? err.message : "Could not load applications"));
  }, [filters]);

  function onFilter(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const nextFilters: AdminApplicationFilters = {
      service_type: (String(form.get("service_type")) || undefined) as AdminApplicationFilters["service_type"],
      status: (String(form.get("status")) || undefined) as AdminApplicationFilters["status"],
      search: String(form.get("search") || "") || undefined,
      created_from: startOfDay(String(form.get("created_from") || "")),
      created_to: endOfDay(String(form.get("created_to") || "")),
      page: 1,
      page_size: 10,
    };
    setFilters(nextFilters);
  }

  const totalPages = Math.max(1, Math.ceil(total / 10));

  return (
    <AdminGuard>
      <PageShell>
        <div>
          <h1 className="text-3xl font-bold text-ink">Applications</h1>
          <p className="mt-2 text-sm text-slate-600">Filter and review all customer applications.</p>
        </div>

        <Card className="mt-6">
          <form onSubmit={onFilter} className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
            <Field label="Service Type">
              <select name="service_type" className={inputClass}>
                <option value="">All services</option>
                <option value="gst_registration">GST Registration</option>
                <option value="fssai_registration">FSSAI Registration</option>
                <option value="udyam_registration">Udyam Registration</option>
              </select>
            </Field>
            <Field label="Status">
              <select name="status" className={inputClass}>
                <option value="">All statuses</option>
                {statuses.map((status) => (
                  <option key={status} value={status}>
                    {status.replaceAll("_", " ")}
                  </option>
                ))}
              </select>
            </Field>
            <Field label="From">
              <input name="created_from" type="date" className={inputClass} />
            </Field>
            <Field label="To">
              <input name="created_to" type="date" className={inputClass} />
            </Field>
            <Field label="Search">
              <input name="search" placeholder="Name, mobile, email, business" className={inputClass} />
            </Field>
            <button className="min-h-11 rounded-md bg-ink px-4 py-2 text-sm font-semibold text-white lg:col-span-5">
              Apply filters
            </button>
          </form>
        </Card>

        {error ? <p className="mt-6 rounded-md bg-red-50 p-3 text-sm text-red-700">{error}</p> : null}

        <Card className="mt-6 overflow-x-auto">
          <table className="w-full min-w-[760px] text-left text-sm">
            <thead className="border-b border-slate-200 text-xs uppercase text-slate-500">
              <tr>
                <th className="py-3 pr-3">Application ID</th>
                <th className="py-3 pr-3">Applicant Name</th>
                <th className="py-3 pr-3">Mobile</th>
                <th className="py-3 pr-3">Service Type</th>
                <th className="py-3 pr-3">Status</th>
                <th className="py-3 pr-3">Created Date</th>
              </tr>
            </thead>
            <tbody>
              {applications.map((application) => (
                <tr key={application.id} className="border-b border-slate-100">
                  <td className="py-3 pr-3">
                    <Link href={`/admin/applications/${application.id}`} className="font-semibold text-saffron">
                      #{application.id}
                    </Link>
                  </td>
                  <td className="py-3 pr-3">{application.proprietor_name || "Not provided"}</td>
                  <td className="py-3 pr-3">{application.applicant_mobile || "Not provided"}</td>
                  <td className="py-3 pr-3">{serviceLabels[application.service_type]}</td>
                  <td className="py-3 pr-3">{application.status.replaceAll("_", " ")}</td>
                  <td className="py-3 pr-3">
                    {new Date(application.created_at).toLocaleDateString("en-IN")}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {applications.length === 0 ? <p className="py-4 text-sm text-slate-600">No applications found.</p> : null}
        </Card>

        <div className="mt-4 flex items-center justify-between">
          <button
            disabled={page <= 1}
            onClick={() => setFilters((current) => ({ ...current, page: page - 1 }))}
            className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold disabled:opacity-50"
          >
            Previous
          </button>
          <p className="text-sm text-slate-600">
            Page {page} of {totalPages}
          </p>
          <button
            disabled={page >= totalPages}
            onClick={() => setFilters((current) => ({ ...current, page: page + 1 }))}
            className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold disabled:opacity-50"
          >
            Next
          </button>
        </div>
      </PageShell>
    </AdminGuard>
  );
}
