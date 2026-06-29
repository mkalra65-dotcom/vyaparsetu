"use client";

import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";
import { Card, Field, PageShell, inputClass } from "@/components/ui";
import { authApi } from "@/lib/api";
import { setToken } from "@/lib/auth";

export default function AdminLoginPage() {
  const router = useRouter();
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setLoading(true);
    const form = new FormData(event.currentTarget);
    try {
      const login = await authApi.login(String(form.get("email")), String(form.get("password")));
      const user = await authApi.me(login.access_token);
      if (!user.is_admin) {
        setError("This account does not have admin access");
        return;
      }
      setToken(login.access_token);
      router.push("/admin");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Admin login failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <PageShell>
      <div className="mx-auto max-w-md">
        <Card>
          <h1 className="text-2xl font-bold text-ink">Admin Login</h1>
          <p className="mt-2 text-sm text-slate-600">Sign in with an admin account to review applications.</p>
          <form onSubmit={onSubmit} className="mt-6 grid gap-4">
            <Field label="Admin email">
              <input name="email" type="email" required className={inputClass} />
            </Field>
            <Field label="Password">
              <input name="password" type="password" required className={inputClass} />
            </Field>
            {error ? <p className="rounded-md bg-red-50 p-3 text-sm text-red-700">{error}</p> : null}
            <button
              type="submit"
              disabled={loading}
              className="min-h-11 rounded-md bg-ink px-4 py-2 text-sm font-semibold text-white disabled:opacity-60"
            >
              {loading ? "Signing in..." : "Login as admin"}
            </button>
          </form>
        </Card>
      </div>
    </PageShell>
  );
}
