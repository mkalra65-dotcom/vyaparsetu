"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";
import { Card, Field, PageShell, inputClass } from "@/components/ui";
import { authApi } from "@/lib/api";
import { setToken } from "@/lib/auth";

export default function LoginPage() {
  const router = useRouter();
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setLoading(true);
    const form = new FormData(event.currentTarget);
    try {
      const response = await authApi.login(String(form.get("email")), String(form.get("password")));
      setToken(response.access_token);
      router.push("/dashboard");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <PageShell>
      <div className="mx-auto max-w-md">
        <Card>
          <h1 className="text-2xl font-bold text-ink">Login</h1>
          <p className="mt-2 text-sm text-slate-600">Continue your VyaparSetu application.</p>
          <form onSubmit={onSubmit} className="mt-6 grid gap-4">
            <Field label="Email">
              <input name="email" type="email" required className={inputClass} />
            </Field>
            <Field label="Password">
              <input name="password" type="password" required className={inputClass} />
            </Field>
            {error ? <p className="text-sm text-red-600">{error}</p> : null}
            <button
              type="submit"
              disabled={loading}
              className="min-h-11 rounded-md bg-ink px-4 py-2 text-sm font-semibold text-white disabled:opacity-60"
            >
              {loading ? "Logging in..." : "Login"}
            </button>
          </form>
          <p className="mt-4 text-sm text-slate-600">
            New to VyaparSetu?{" "}
            <Link href="/auth/register" className="font-semibold text-leaf">
              Register
            </Link>
          </p>
        </Card>
      </div>
    </PageShell>
  );
}
