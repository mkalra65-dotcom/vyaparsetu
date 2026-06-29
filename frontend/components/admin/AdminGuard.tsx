"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { authApi } from "@/lib/api";
import { clearToken, getToken } from "@/lib/auth";
import type { User } from "@/types/api";

export function AdminGuard({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const [ready, setReady] = useState(false);
  const [user, setUser] = useState<User | null>(null);

  useEffect(() => {
    const token = getToken();
    if (!token) {
      router.push("/admin/login");
      return;
    }
    authApi
      .me(token)
      .then((currentUser) => {
        if (!currentUser.is_admin) {
          clearToken();
          router.push("/admin/login");
          return;
        }
        setUser(currentUser);
        setReady(true);
      })
      .catch(() => {
        clearToken();
        router.push("/admin/login");
      });
  }, [router]);

  if (!ready) {
    return <p className="p-6 text-sm text-slate-600">Checking admin access...</p>;
  }

  return (
    <div>
      <div className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3">
          <p className="text-sm font-semibold text-ink">Admin: {user?.email}</p>
          <button
            onClick={() => {
              clearToken();
              router.push("/admin/login");
            }}
            className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold"
          >
            Logout
          </button>
        </div>
      </div>
      {children}
    </div>
  );
}
