"use client";

import { useParams } from "next/navigation";
import { FormEvent, useEffect, useState } from "react";
import { AdminGuard } from "@/components/admin/AdminGuard";
import { AuditTimeline } from "@/components/admin/AuditTimeline";
import { Card, Field, PageShell, inputClass } from "@/components/ui";
import { adminApi } from "@/lib/api";
import { getToken } from "@/lib/auth";
import type { AdminApplicationDetail, ApplicationStatus, DocumentMetadata } from "@/types/api";

const allowedStatuses: Exclude<ApplicationStatus, "draft">[] = [
  "documents_pending",
  "under_review",
  "clarification_required",
  "ready_for_filing",
  "filing_in_progress",
  "filed",
  "approved",
  "rejected",
  "certificate_delivered",
  "completed",
];

const serviceLabels: Record<string, string> = {
  gst_registration: "GST Registration",
  fssai_registration: "FSSAI Registration",
  udyam_registration: "Udyam Registration",
};

function DetailRow({ label, value }: { label: string; value: string | number | null | undefined }) {
  return (
    <div className="rounded-md bg-slate-50 p-3">
      <p className="text-xs font-semibold uppercase text-slate-500">{label}</p>
      <p className="mt-1 text-sm text-ink">{value || "Not provided"}</p>
    </div>
  );
}

export default function AdminApplicationReviewPage() {
  const params = useParams<{ id: string }>();
  const [application, setApplication] = useState<AdminApplicationDetail | null>(null);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  async function load() {
    const token = getToken();
    if (!token) return;
    const response = await adminApi.applicationDetail(token, params.id);
    setApplication(response);
  }

  useEffect(() => {
    load().catch((err) => setError(err instanceof Error ? err.message : "Could not load application"));
  }, [params.id]);

  async function updateStatus(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setSuccess("");
    const token = getToken();
    if (!token) return;
    const form = new FormData(event.currentTarget);
    const status = String(form.get("status")) as Exclude<ApplicationStatus, "draft">;
    const customerMessage = String(form.get("customer_clarification_message") || "");
    if (status === "clarification_required" && !customerMessage.trim()) {
      setError("Clarification message is required for clarification_required status");
      return;
    }
    try {
      const response = await adminApi.updateStatus(token, params.id, {
        status,
        customer_clarification_message: customerMessage || null,
        note: String(form.get("note") || "") || null,
      });
      setApplication(response);
      setSuccess("Status updated");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not update status");
    }
  }

  async function updateNotes(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setSuccess("");
    const token = getToken();
    if (!token) return;
    const form = new FormData(event.currentTarget);
    try {
      const response = await adminApi.updateNotes(token, params.id, {
        internal_admin_notes: String(form.get("internal_admin_notes") || "") || null,
        customer_clarification_message:
          String(form.get("customer_clarification_message") || "") || null,
      });
      setApplication(response);
      setSuccess("Notes updated");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not update notes");
    }
  }

  async function createQuery(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setSuccess("");
    const token = getToken();
    if (!token) return;
    const form = new FormData(event.currentTarget);
    try {
      const response = await adminApi.createGovernmentQuery(token, params.id, {
        message: String(form.get("message") || ""),
        required_document_type: String(form.get("required_document_type") || ""),
        due_date: String(form.get("due_date") || ""),
      });
      setApplication(response);
      setSuccess("Government query sent");
      event.currentTarget.reset();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not create query");
    }
  }

  async function createTimelineEvent(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setSuccess("");
    const token = getToken();
    if (!token) return;
    const form = new FormData(event.currentTarget);
    const eventType = String(form.get("event_type") || "");
    try {
      const response = await adminApi.createTimelineEvent(token, params.id, {
        event_type: eventType,
        title: eventType.replaceAll("_", " "),
        description: String(form.get("description") || "") || null,
      });
      setApplication(response);
      setSuccess("Timeline updated");
      event.currentTarget.reset();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not create timeline event");
    }
  }

  async function uploadCertificate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setSuccess("");
    const token = getToken();
    if (!token) return;
    const form = new FormData(event.currentTarget);
    const file = form.get("file");
    if (!(file instanceof File)) {
      setError("Certificate file is required");
      return;
    }
    try {
      const response = await adminApi.uploadCertificate(
        token,
        params.id,
        String(form.get("certificate_type") || ""),
        file,
      );
      setApplication(response);
      setSuccess("Certificate uploaded");
      event.currentTarget.reset();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not upload certificate");
    }
  }

  async function deliverCertificate(certificateId: number) {
    setError("");
    setSuccess("");
    const token = getToken();
    if (!token) return;
    try {
      const response = await adminApi.deliverCertificate(token, certificateId);
      setApplication(response);
      setSuccess("Certificate delivered");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not deliver certificate");
    }
  }

  async function downloadDocument(document: DocumentMetadata) {
    const token = getToken();
    if (!token) return;
    try {
      const blob = await adminApi.downloadDocument(token, document.id);
      const url = URL.createObjectURL(blob);
      const link = window.document.createElement("a");
      link.href = url;
      link.download = document.original_filename;
      link.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not download document");
    }
  }

  if (!application) {
    return (
      <AdminGuard>
        <PageShell>
          <p className="text-sm text-slate-600">{error || "Loading application..."}</p>
        </PageShell>
      </AdminGuard>
    );
  }

  return (
    <AdminGuard>
      <PageShell>
        <div>
          <p className="text-sm font-semibold text-leaf">{serviceLabels[application.service_type]}</p>
          <h1 className="mt-1 text-3xl font-bold text-ink">Application #{application.id}</h1>
          <p className="mt-2 text-sm text-slate-600">
            {application.business_name} · {application.status.replaceAll("_", " ")}
          </p>
        </div>

        {error ? <p className="mt-6 rounded-md bg-red-50 p-3 text-sm text-red-700">{error}</p> : null}
        {success ? <p className="mt-6 rounded-md bg-green-50 p-3 text-sm text-green-700">{success}</p> : null}

        <div className="mt-6 grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
          <Card>
            <h2 className="text-xl font-bold text-ink">Full application details</h2>
            <div className="mt-4 grid gap-3 sm:grid-cols-2">
              <DetailRow label="Applicant Name" value={application.proprietor_name} />
              <DetailRow label="Mobile" value={application.applicant_mobile} />
              <DetailRow label="Email" value={application.applicant_email} />
              <DetailRow label="PAN" value={application.pan_number} />
              <DetailRow label="Aadhaar" value={application.aadhaar_number} />
              <DetailRow label="Business Name" value={application.business_name} />
              <DetailRow label="Business Type" value={application.business_type} />
              <DetailRow label="Address" value={application.business_address} />
              <DetailRow label="City" value={application.city} />
              <DetailRow label="State" value={application.state} />
              <DetailRow label="Pincode" value={application.pincode} />
              <DetailRow label="Business Constitution" value={application.business_constitution} />
              <DetailRow label="Nature of Business" value={application.nature_of_business} />
              <DetailRow label="Food Business Type" value={application.food_business_type} />
              <DetailRow label="Food Category" value={application.food_category} />
              <DetailRow label="Enterprise Name" value={application.enterprise_name} />
              <DetailRow label="Organisation Type" value={application.type_of_organisation} />
              <DetailRow label="Major Activity" value={application.major_activity} />
              <DetailRow label="NIC Code" value={application.nic_code} />
              <DetailRow label="Investment Amount" value={application.investment_amount} />
              <DetailRow label="Turnover" value={application.turnover || application.annual_turnover} />
            </div>
          </Card>

          <div className="grid gap-6">
            <Card>
              <h2 className="text-xl font-bold text-ink">Change status</h2>
              <form onSubmit={updateStatus} className="mt-4 grid gap-4">
                <Field label="Status">
                  <select name="status" defaultValue={application.status} className={inputClass}>
                    {allowedStatuses.map((status) => (
                      <option key={status} value={status}>
                        {status.replaceAll("_", " ")}
                      </option>
                    ))}
                  </select>
                </Field>
                <Field label="Clarification message">
                  <textarea
                    name="customer_clarification_message"
                    defaultValue={application.customer_clarification_message || ""}
                    className={`${inputClass} min-h-24`}
                  />
                </Field>
                <Field label="Status note">
                  <input name="note" className={inputClass} />
                </Field>
                <button className="min-h-11 rounded-md bg-saffron px-4 py-2 text-sm font-semibold text-white">
                  Update status
                </button>
              </form>
            </Card>

            <Card>
              <h2 className="text-xl font-bold text-ink">Notes</h2>
              <form onSubmit={updateNotes} className="mt-4 grid gap-4">
                <Field label="Internal note">
                  <textarea
                    name="internal_admin_notes"
                    defaultValue={application.internal_admin_notes || ""}
                    className={`${inputClass} min-h-24`}
                  />
                </Field>
                <Field label="Customer clarification message">
                  <textarea
                    name="customer_clarification_message"
                    defaultValue={application.customer_clarification_message || ""}
                    className={`${inputClass} min-h-24`}
                  />
                </Field>
                <button className="min-h-11 rounded-md bg-ink px-4 py-2 text-sm font-semibold text-white">
                  Save notes
                </button>
              </form>
            </Card>

            <Card>
              <h2 className="text-xl font-bold text-ink">Government query</h2>
              <form onSubmit={createQuery} className="mt-4 grid gap-4">
                <Field label="Required document">
                  <select name="required_document_type" className={inputClass} required>
                    {application.required_documents.map((documentType) => (
                      <option key={documentType} value={documentType}>
                        {documentType.replaceAll("_", " ")}
                      </option>
                    ))}
                  </select>
                </Field>
                <Field label="Due date">
                  <input name="due_date" type="date" className={inputClass} required />
                </Field>
                <Field label="Message">
                  <textarea name="message" className={`${inputClass} min-h-24`} required />
                </Field>
                <button className="min-h-11 rounded-md bg-saffron px-4 py-2 text-sm font-semibold text-white">
                  Send query
                </button>
              </form>
            </Card>

            <Card>
              <h2 className="text-xl font-bold text-ink">Timeline action</h2>
              <form onSubmit={createTimelineEvent} className="mt-4 grid gap-4">
                <Field label="Event">
                  <select name="event_type" className={inputClass}>
                    <option value="review_started">Review started</option>
                    <option value="filing_submitted">Filing submitted</option>
                    <option value="certificate_delivered">Certificate delivered</option>
                  </select>
                </Field>
                <Field label="Description">
                  <input name="description" className={inputClass} />
                </Field>
                <button className="min-h-11 rounded-md bg-ink px-4 py-2 text-sm font-semibold text-white">
                  Add event
                </button>
              </form>
            </Card>

            <Card>
              <h2 className="text-xl font-bold text-ink">Certificate</h2>
              <form onSubmit={uploadCertificate} className="mt-4 grid gap-4">
                <Field label="Certificate type">
                  <select name="certificate_type" className={inputClass}>
                    <option value="gst_certificate">GST Certificate</option>
                    <option value="fssai_certificate">FSSAI Certificate</option>
                    <option value="udyam_certificate">Udyam Certificate</option>
                  </select>
                </Field>
                <Field label="Certificate file">
                  <input name="file" type="file" accept=".pdf,.jpg,.jpeg,.png" className={inputClass} required />
                </Field>
                <button className="min-h-11 rounded-md bg-leaf px-4 py-2 text-sm font-semibold text-white">
                  Upload certificate
                </button>
              </form>
            </Card>
          </div>
        </div>

        <div className="mt-6 grid gap-6 lg:grid-cols-2">
          <Card>
            <h2 className="text-xl font-bold text-ink">AI review summary</h2>
            <p className="mt-4 text-4xl font-bold text-leaf">
              {application.health_score ?? "Pending"}
              {application.health_score !== null ? "/100" : ""}
            </p>
            <p className="mt-3 text-sm leading-6 text-slate-700">
              {application.ai_review_summary || "Document intelligence has not generated a summary yet."}
            </p>
          </Card>

          <Card>
            <h2 className="text-xl font-bold text-ink">Missing required documents</h2>
            <div className="mt-4 grid gap-2">
              {application.missing_required_documents.length ? (
                application.missing_required_documents.map((documentType) => (
                  <p key={documentType} className="rounded-md bg-amber-50 px-3 py-2 text-sm text-amber-800">
                    {documentType.replaceAll("_", " ")}
                  </p>
                ))
              ) : (
                <p className="text-sm text-slate-600">No required documents are missing.</p>
              )}
            </div>
          </Card>

          <Card>
            <h2 className="text-xl font-bold text-ink">Application timeline</h2>
            <div className="mt-4 grid gap-3">
              {application.timeline_events.length ? (
                application.timeline_events.map((event) => (
                  <div key={event.id} className="border-l-2 border-leaf pl-4">
                    <p className="font-semibold text-ink">{event.title}</p>
                    {event.description ? <p className="mt-1 text-sm text-slate-700">{event.description}</p> : null}
                    <p className="mt-1 text-xs text-slate-500">
                      {new Date(event.created_at).toLocaleString("en-IN")} · {event.source_channel}
                    </p>
                  </div>
                ))
              ) : (
                <p className="text-sm text-slate-600">No timeline events yet.</p>
              )}
            </div>
          </Card>

          <Card>
            <h2 className="text-xl font-bold text-ink">Government queries</h2>
            <div className="mt-4 grid gap-3">
              {application.government_queries.length ? (
                application.government_queries.map((query) => (
                  <div
                    key={query.id}
                    className={`rounded-md border p-3 ${
                      query.is_overdue ? "border-red-200 bg-red-50" : "border-slate-200 bg-white"
                    }`}
                  >
                    <p className="font-semibold text-ink">{query.required_document_type.replaceAll("_", " ")}</p>
                    <p className="mt-1 text-sm text-slate-700">{query.message}</p>
                    <p className="mt-2 text-xs font-semibold text-slate-600">
                      Due {new Date(query.due_date).toLocaleDateString("en-IN")} · {query.status}
                    </p>
                  </div>
                ))
              ) : (
                <p className="text-sm text-slate-600">No government queries.</p>
              )}
            </div>
          </Card>

          <Card>
            <h2 className="text-xl font-bold text-ink">Audit log</h2>
            <div className="mt-4">
              <AuditTimeline logs={application.audit_logs} />
            </div>
          </Card>
        </div>

        <Card className="mt-6 overflow-x-auto">
          <h2 className="text-xl font-bold text-ink">Certificates</h2>
          <table className="mt-4 w-full min-w-[760px] text-left text-sm">
            <thead className="border-b border-slate-200 text-xs uppercase text-slate-500">
              <tr>
                <th className="py-3 pr-3">Type</th>
                <th className="py-3 pr-3">Filename</th>
                <th className="py-3 pr-3">Uploaded</th>
                <th className="py-3 pr-3">Delivered</th>
                <th className="py-3 pr-3">Action</th>
              </tr>
            </thead>
            <tbody>
              {application.certificates.map((certificate) => (
                <tr key={certificate.id} className="border-b border-slate-100">
                  <td className="py-3 pr-3">{certificate.certificate_type.replaceAll("_", " ")}</td>
                  <td className="py-3 pr-3">{certificate.original_filename}</td>
                  <td className="py-3 pr-3">{new Date(certificate.uploaded_at).toLocaleString("en-IN")}</td>
                  <td className="py-3 pr-3">
                    {certificate.delivered_at ? new Date(certificate.delivered_at).toLocaleString("en-IN") : "Pending"}
                  </td>
                  <td className="py-3 pr-3">
                    <button
                      onClick={() => deliverCertificate(certificate.id)}
                      className="font-semibold text-saffron disabled:text-slate-400"
                      disabled={Boolean(certificate.delivered_at)}
                    >
                      Deliver Certificate
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {application.certificates.length === 0 ? (
            <p className="mt-4 text-sm text-slate-600">No certificates uploaded yet.</p>
          ) : null}
        </Card>

        <Card className="mt-6">
          <h2 className="text-xl font-bold text-ink">Customer feedback</h2>
          <div className="mt-4 grid gap-3">
            {application.feedback.length ? (
              application.feedback.map((feedback) => (
                <div key={feedback.id} className="rounded-md border border-slate-200 p-3">
                  <p className="font-semibold text-ink">Rating {feedback.rating}/5</p>
                  {feedback.feedback ? <p className="mt-1 text-sm text-slate-700">{feedback.feedback}</p> : null}
                  <p className="mt-1 text-xs text-slate-500">
                    {new Date(feedback.created_at).toLocaleString("en-IN")}
                  </p>
                </div>
              ))
            ) : (
              <p className="text-sm text-slate-600">No feedback yet.</p>
            )}
          </div>
        </Card>

        <Card className="mt-6 overflow-x-auto">
          <h2 className="text-xl font-bold text-ink">Uploaded documents</h2>
          <table className="mt-4 w-full min-w-[860px] text-left text-sm">
            <thead className="border-b border-slate-200 text-xs uppercase text-slate-500">
              <tr>
                <th className="py-3 pr-3">Type</th>
                <th className="py-3 pr-3">Filename</th>
                <th className="py-3 pr-3">MIME</th>
                <th className="py-3 pr-3">Source</th>
                <th className="py-3 pr-3">Size</th>
                <th className="py-3 pr-3">Uploaded By</th>
                <th className="py-3 pr-3">Action</th>
              </tr>
            </thead>
            <tbody>
              {application.documents.map((document) => (
                <tr key={document.id} className="border-b border-slate-100">
                  <td className="py-3 pr-3">{document.document_type.replaceAll("_", " ")}</td>
                  <td className="py-3 pr-3">{document.original_filename}</td>
                  <td className="py-3 pr-3">{document.mime_type}</td>
                  <td className="py-3 pr-3">{document.source_channel}</td>
                  <td className="py-3 pr-3">{(document.file_size / 1024).toFixed(1)} KB</td>
                  <td className="py-3 pr-3">User #{document.uploaded_by_user_id}</td>
                  <td className="py-3 pr-3">
                    <button onClick={() => downloadDocument(document)} className="font-semibold text-saffron">
                      Download
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {application.documents.length === 0 ? (
            <p className="mt-4 text-sm text-slate-600">No documents uploaded yet.</p>
          ) : null}
        </Card>

        <Card className="mt-6">
          <h2 className="text-xl font-bold text-ink">Extracted document data</h2>
          <div className="mt-4 grid gap-4">
            {application.documents.map((document) => (
              <div key={document.id} className="rounded-md border border-slate-200 p-4">
                <p className="font-semibold text-ink">{document.document_type.replaceAll("_", " ")}</p>
                {document.extractions.length ? (
                  document.extractions.map((extraction) => (
                    <div key={extraction.id} className="mt-3 rounded-md bg-slate-50 p-3">
                      <p className="text-sm text-slate-700">
                        Provider: {extraction.provider} · Confidence:{" "}
                        {(extraction.confidence_score * 100).toFixed(0)}%
                      </p>
                      <dl className="mt-3 grid gap-2 sm:grid-cols-2">
                        {Object.entries(extraction.extracted_json.extracted_fields).map(([key, value]) => (
                          <div key={key}>
                            <dt className="text-xs font-semibold uppercase text-slate-500">
                              {key.replaceAll("_", " ")}
                            </dt>
                            <dd className="text-sm text-ink">{value || "Not detected"}</dd>
                          </div>
                        ))}
                      </dl>
                      {extraction.validation_warnings.length ? (
                        <div className="mt-3 grid gap-2">
                          {extraction.validation_warnings.map((warning) => (
                            <p key={warning} className="rounded-md bg-amber-50 px-3 py-2 text-sm text-amber-800">
                              {warning}
                            </p>
                          ))}
                        </div>
                      ) : (
                        <p className="mt-3 text-sm text-green-700">No validation warnings.</p>
                      )}
                    </div>
                  ))
                ) : (
                  <p className="mt-2 text-sm text-slate-600">
                    {document.ai_processing_status === "manual_review"
                      ? "Document intelligence is disabled. Review this document manually."
                      : "Extraction is pending."}
                  </p>
                )}
              </div>
            ))}
          </div>
        </Card>
      </PageShell>
    </AdminGuard>
  );
}
