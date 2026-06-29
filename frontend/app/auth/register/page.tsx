"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";
import { Card, Field, PageShell, inputClass } from "@/components/ui";
import { authApi } from "@/lib/api";

export default function RegisterPage() {
  const router = useRouter();
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setLoading(true);
    const form = new FormData(event.currentTarget);
    try {
      await authApi.register({
        full_name: String(form.get("full_name")),
        email: String(form.get("email")),
        password: String(form.get("password")),
      });
      router.push("/auth/login");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Registration failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <PageShell>
      <div className="mx-auto max-w-md">
        <Card>
          <h1 className="text-2xl font-bold text-ink">Register</h1>
          <p className="mt-2 text-sm text-slate-600">Create your customer account.</p>
          <form onSubmit={onSubmit} className="mt-6 grid gap-4">
            <Field label="Applicant name">
              <input name="full_name" required className={inputClass} />
            </Field>
            <Field label="Email">
              <input name="email" type="email" required className={inputClass} />
            </Field>
            <Field label="Password">
              <input name="password" type="password" required minLength={8} className={inputClass} />
            </Field>
            {error ? <p className="text-sm text-red-600">{error}</p> : null}
            <button
              type="submit"
              disabled={loading}
              className="min-h-11 rounded-md bg-saffron px-4 py-2 text-sm font-semibold text-white disabled:opacity-60"
            >
              {loading ? "Creating account..." : "Register"}
            </button>
          </form>
          <p className="mt-4 text-sm text-slate-600">
            Already registered?{" "}
            <Link href="/auth/login" className="font-semibold text-leaf">
              Login
            </Link>
          </p>
        </Card>
      </div>
    </PageShell>
  );
}
