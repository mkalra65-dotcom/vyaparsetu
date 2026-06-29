"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { Card, PageShell } from "@/components/ui";
import { notificationApi } from "@/lib/api";
import { getToken } from "@/lib/auth";
import type { Notification } from "@/types/api";

export default function NotificationsPage() {
  const router = useRouter();
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [error, setError] = useState("");

  async function load(token: string) {
    const response = await notificationApi.mine(token);
    setNotifications(response);
  }

  useEffect(() => {
    const token = getToken();
    if (!token) {
      router.push("/auth/login");
      return;
    }
    load(token).catch((err) => setError(err instanceof Error ? err.message : "Could not load notifications"));
  }, [router]);

  async function markRead(notificationId: number) {
    const token = getToken();
    if (!token) return;
    const updated = await notificationApi.markRead(token, notificationId);
    setNotifications((current) =>
      current.map((notification) => (notification.id === updated.id ? updated : notification)),
    );
  }

  return (
    <PageShell>
      <h1 className="text-3xl font-bold text-ink">Notifications</h1>
      <p className="mt-2 text-sm text-slate-600">Updates about your applications and documents.</p>
      {error ? <p className="mt-6 rounded-md bg-red-50 p-3 text-sm text-red-700">{error}</p> : null}
      <div className="mt-6 grid gap-4">
        {notifications.length === 0 ? <Card>No notifications yet.</Card> : null}
        {notifications.map((notification) => (
          <Card key={notification.id} className={notification.is_read ? "opacity-75" : ""}>
            <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
              <div>
                <p className="text-sm font-semibold text-ink">{notification.subject}</p>
                <p className="mt-1 text-sm leading-6 text-slate-600">{notification.message}</p>
                <p className="mt-2 text-xs text-slate-500">
                  {new Date(notification.created_at).toLocaleString("en-IN")} ·{" "}
                  {notification.is_read ? "Read" : "Unread"}
                </p>
              </div>
              <div className="flex gap-2">
                {notification.application_id ? (
                  <Link
                    href={`/applications/${notification.application_id}`}
                    className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold"
                  >
                    View
                  </Link>
                ) : null}
                {!notification.is_read ? (
                  <button
                    onClick={() => markRead(notification.id)}
                    className="rounded-md bg-ink px-3 py-2 text-sm font-semibold text-white"
                  >
                    Mark read
                  </button>
                ) : null}
              </div>
            </div>
          </Card>
        ))}
      </div>
    </PageShell>
  );
}
