"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { AdminGuard } from "@/components/admin/AdminGuard";
import { Card, PageShell } from "@/components/ui";
import { adminApi } from "@/lib/api";
import { getToken } from "@/lib/auth";
import type { Notification } from "@/types/api";

export default function AdminNotificationsPage() {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    const token = getToken();
    if (!token) return;
    adminApi
      .notifications(token)
      .then(setNotifications)
      .catch((err) => setError(err instanceof Error ? err.message : "Could not load notifications"));
  }, []);

  return (
    <AdminGuard>
      <PageShell>
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="text-3xl font-bold text-ink">Admin notifications</h1>
            <p className="mt-2 text-sm text-slate-600">Recent application and document review events.</p>
          </div>
          <Link href="/admin/applications" className="rounded-md bg-saffron px-4 py-2 text-sm font-semibold text-white">
            Applications
          </Link>
        </div>
        {error ? <p className="mt-6 rounded-md bg-red-50 p-3 text-sm text-red-700">{error}</p> : null}
        <div className="mt-6 grid gap-4">
          {notifications.length === 0 ? <Card>No notifications yet.</Card> : null}
          {notifications.map((notification) => (
            <Card key={notification.id}>
              <div className="grid gap-3 sm:grid-cols-[1fr_auto] sm:items-start">
                <div>
                  <p className="text-sm font-semibold text-ink">{notification.subject}</p>
                  <p className="mt-1 text-sm leading-6 text-slate-600">{notification.message}</p>
                  <p className="mt-2 text-xs text-slate-500">
                    {new Date(notification.created_at).toLocaleString("en-IN")} · {notification.status} ·{" "}
                    {notification.provider}
                  </p>
                </div>
                {notification.application_id ? (
                  <Link
                    href={`/admin/applications/${notification.application_id}`}
                    className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold"
                  >
                    Review
                  </Link>
                ) : null}
              </div>
            </Card>
          ))}
        </div>
      </PageShell>
    </AdminGuard>
  );
}
