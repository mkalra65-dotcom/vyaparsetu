"use client";

import { useParams, useRouter } from "next/navigation";
import { FormEvent, useEffect, useState } from "react";
import { Card, Field, PageShell, inputClass } from "@/components/ui";
import { applicationApi, certificateApi } from "@/lib/api";
import { getToken } from "@/lib/auth";
import type { ApplicationTracking, Certificate } from "@/types/api";

export default function ApplicationTrackingPage() {
  const router = useRouter();
  const params = useParams<{ id: string }>();
  const [tracking, setTracking] = useState<ApplicationTracking | null>(null);
  const [token, setToken] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  useEffect(() => {
    const token = getToken();
    if (!token) {
      router.push("/auth/login");
      return;
    }
    setToken(token);
    applicationApi
      .tracking(token, params.id)
      .then(setTracking)
      .catch((err) => setError(err instanceof Error ? err.message : "Could not load tracking"));
  }, [params.id, router]);

  async function downloadCertificate(certificate: Certificate) {
    setError("");
    try {
      const blob = await certificateApi.download(token, certificate.id);
      const url = URL.createObjectURL(blob);
      const link = window.document.createElement("a");
      link.href = url;
      link.download = certificate.original_filename;
      link.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not download certificate");
    }
  }

  async function submitFeedback(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setSuccess("");
    const form = new FormData(event.currentTarget);
    try {
      const feedback = await certificateApi.submitFeedback(token, params.id, {
        rating: Number(form.get("rating")),
        feedback: String(form.get("feedback") || "") || null,
      });
      setTracking((current) =>
        current ? { ...current, feedback: [feedback, ...current.feedback] } : current,
      );
      setSuccess("Feedback submitted");
      event.currentTarget.reset();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not submit feedback");
    }
  }

  if (!tracking) {
    return (
      <PageShell>
        <p className="text-sm text-slate-600">{error || "Loading tracking..."}</p>
      </PageShell>
    );
  }

  return (
    <PageShell>
      <div>
        <p className="text-sm font-semibold text-leaf">Application #{tracking.application.id}</p>
        <h1 className="mt-1 text-3xl font-bold text-ink">{tracking.application.business_name}</h1>
        <p className="mt-2 text-sm text-slate-600">
          Current status: {tracking.application.status.replaceAll("_", " ")}
        </p>
      </div>

      {error ? <p className="mt-6 rounded-md bg-red-50 p-3 text-sm text-red-700">{error}</p> : null}
      {success ? <p className="mt-6 rounded-md bg-green-50 p-3 text-sm text-green-700">{success}</p> : null}

      <div className="mt-6 grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
        <Card>
          <h2 className="text-xl font-bold text-ink">Timeline</h2>
          <div className="mt-4 grid gap-3">
            {tracking.timeline_events.length === 0 ? (
              <p className="text-sm text-slate-600">No timeline events yet.</p>
            ) : null}
            {tracking.timeline_events.map((event) => (
              <div key={event.id} className="border-l-2 border-leaf pl-4">
                <p className="font-semibold text-ink">{event.title}</p>
                {event.description ? <p className="mt-1 text-sm text-slate-700">{event.description}</p> : null}
                <p className="mt-1 text-xs text-slate-500">
                  {new Date(event.created_at).toLocaleString("en-IN")} · {event.source_channel}
                </p>
              </div>
            ))}
          </div>
        </Card>

        <Card>
          <h2 className="text-xl font-bold text-ink">Government queries</h2>
          <div className="mt-4 grid gap-3">
            {tracking.government_queries.length === 0 ? (
              <p className="text-sm text-slate-600">No government queries.</p>
            ) : null}
            {tracking.government_queries.map((query) => (
              <div
                key={query.id}
                className={`rounded-md border p-3 ${
                  query.is_overdue ? "border-red-200 bg-red-50" : "border-slate-200 bg-white"
                }`}
              >
                <p className="font-semibold text-ink">{query.required_document_type.replaceAll("_", " ")}</p>
                <p className="mt-1 text-sm leading-6 text-slate-700">{query.message}</p>
                <p className="mt-2 text-xs font-semibold text-slate-600">
                  Due {new Date(query.due_date).toLocaleDateString("en-IN")} · {query.status}
                </p>
                {query.is_overdue ? <p className="mt-2 text-sm text-red-700">Response is overdue.</p> : null}
              </div>
            ))}
          </div>
        </Card>
      </div>

      <Card className="mt-6">
        <h2 className="text-xl font-bold text-ink">Certificates</h2>
        <div className="mt-4 grid gap-3">
          {tracking.certificates.length === 0 ? (
            <p className="text-sm text-slate-600">No certificates uploaded yet.</p>
          ) : null}
          {tracking.certificates.map((certificate) => (
            <div key={certificate.id} className="rounded-md border border-slate-200 p-3">
              <p className="font-semibold text-ink">{certificate.certificate_type.replaceAll("_", " ")}</p>
              <p className="mt-1 text-sm text-slate-600">{certificate.original_filename}</p>
              <p className="mt-1 text-xs text-slate-500">
                Uploaded {new Date(certificate.uploaded_at).toLocaleString("en-IN")}
                {certificate.delivered_at
                  ? ` · Delivered ${new Date(certificate.delivered_at).toLocaleString("en-IN")}`
                  : ""}
              </p>
              <button
                onClick={() => downloadCertificate(certificate)}
                className="mt-3 min-h-10 rounded-md bg-saffron px-3 py-2 text-sm font-semibold text-white"
              >
                Download certificate
              </button>
            </div>
          ))}
        </div>
      </Card>

      {tracking.certificates.some((certificate) => certificate.delivered_at) ? (
        <Card className="mt-6">
          <h2 className="text-xl font-bold text-ink">Feedback</h2>
          {tracking.feedback.length ? (
            <div className="mt-4 grid gap-3">
              {tracking.feedback.map((feedback) => (
                <div key={feedback.id} className="rounded-md border border-slate-200 p-3">
                  <p className="font-semibold text-ink">Rating {feedback.rating}/5</p>
                  {feedback.feedback ? <p className="mt-1 text-sm text-slate-700">{feedback.feedback}</p> : null}
                </div>
              ))}
            </div>
          ) : (
            <form onSubmit={submitFeedback} className="mt-4 grid gap-4">
              <Field label="Rating">
                <select name="rating" className={inputClass}>
                  {[5, 4, 3, 2, 1].map((rating) => (
                    <option key={rating} value={rating}>
                      {rating}
                    </option>
                  ))}
                </select>
              </Field>
              <Field label="Feedback">
                <textarea name="feedback" className={`${inputClass} min-h-24`} />
              </Field>
              <button className="min-h-11 rounded-md bg-ink px-4 py-2 text-sm font-semibold text-white">
                Submit feedback
              </button>
            </form>
          )}
        </Card>
      ) : null}

      <Card className="mt-6">
        <h2 className="text-xl font-bold text-ink">Documents</h2>
        <div className="mt-4 grid gap-3 sm:grid-cols-2">
          {tracking.documents.map((document) => (
            <div key={document.id} className="rounded-md border border-slate-200 p-3">
              <p className="font-semibold text-ink">{document.document_type.replaceAll("_", " ")}</p>
              <p className="mt-1 text-sm text-slate-600">{document.original_filename}</p>
              <p className="mt-1 text-xs text-slate-500">{document.source_channel}</p>
            </div>
          ))}
        </div>
      </Card>
    </PageShell>
  );
}
