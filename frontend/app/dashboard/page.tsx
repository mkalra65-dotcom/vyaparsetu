"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { ButtonLink, Card, PageShell } from "@/components/ui";
import { applicationApi, notificationApi } from "@/lib/api";
import { clearToken, getToken } from "@/lib/auth";
import type { Application } from "@/types/api";
import type { Notification } from "@/types/api";

const serviceLabels: Record<string, string> = {
  gst_registration: "GST Registration",
  fssai_registration: "FSSAI Registration",
  udyam_registration: "Udyam Registration",
};

export default function DashboardPage() {
  const router = useRouter();
  const [applications, setApplications] = useState<Application[]>([]);
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    const token = getToken();
    if (!token) {
      router.push("/auth/login");
      return;
    }
    applicationApi
      .mine(token)
      .then(setApplications)
      .catch((err) => setError(err instanceof Error ? err.message : "Could not load applications"));
    notificationApi.mine(token).then(setNotifications).catch(() => undefined);
  }, [router]);

  function logout() {
    clearToken();
    router.push("/");
  }

  return (
    <PageShell>
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-3xl font-bold text-ink">Customer dashboard</h1>
          <p className="mt-2 text-sm text-slate-600">Track your registrations and upload documents.</p>
        </div>
        <div className="flex gap-2">
          <Link href="/notifications" className="rounded-md border border-slate-300 px-4 py-2 text-sm font-semibold">
            Notifications ({notifications.filter((notification) => !notification.is_read).length})
          </Link>
          <ButtonLink href="/applications/new">Start Application</ButtonLink>
          <button onClick={logout} className="rounded-md border border-slate-300 px-4 py-2 text-sm font-semibold">
            Logout
          </button>
        </div>
      </div>

      {error ? <p className="mt-6 rounded-md bg-red-50 p-3 text-sm text-red-700">{error}</p> : null}

      <div className="mt-6 grid gap-4">
        {notifications.length ? (
          <Card>
            <div className="flex items-center justify-between gap-3">
              <div>
                <h2 className="text-lg font-bold text-ink">Recent notifications</h2>
                <p className="mt-1 text-sm text-slate-600">{notifications[0].subject}</p>
              </div>
              <Link href="/notifications" className="text-sm font-semibold text-saffron">
                View all
              </Link>
            </div>
          </Card>
        ) : null}
        {applications.length === 0 && !error ? (
          <Card>
            <p className="text-sm text-slate-600">No applications yet.</p>
          </Card>
        ) : null}
        {applications.map((application) => (
          <Card key={application.id}>
            <div className="grid gap-3 sm:grid-cols-[1fr_auto] sm:items-center">
              <div>
                <h2 className="text-lg font-bold text-ink">{application.business_name}</h2>
                <p className="text-sm text-slate-600">{serviceLabels[application.service_type]}</p>
                <p className="mt-1 text-sm text-slate-600">
                  Created {new Date(application.created_at).toLocaleDateString("en-IN")}
                </p>
              </div>
              <div className="grid gap-2 sm:justify-items-end">
                <span className="rounded-full bg-mist px-3 py-1 text-xs font-semibold text-leaf">
                  {application.status.replaceAll("_", " ")}
                </span>
                <Link href={`/applications/${application.id}`} className="text-sm font-semibold text-saffron">
                  Continue / view application
                </Link>
              </div>
            </div>
          </Card>
        ))}
      </div>
    </PageShell>
  );
}
