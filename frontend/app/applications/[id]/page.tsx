"use client";

import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { Card, PageShell } from "@/components/ui";
import { DocumentUpload } from "@/components/DocumentUpload";
import { applicationApi } from "@/lib/api";
import { getToken } from "@/lib/auth";
import type { Application, DocumentMetadata } from "@/types/api";

const serviceLabels: Record<string, string> = {
  gst_registration: "GST Registration",
  fssai_registration: "FSSAI Registration",
  udyam_registration: "Udyam Registration",
};

export default function ApplicationDetailPage() {
  const router = useRouter();
  const params = useParams<{ id: string }>();
  const [token, setTokenState] = useState("");
  const [application, setApplication] = useState<Application | null>(null);
  const [documents, setDocuments] = useState<DocumentMetadata[]>([]);
  const [error, setError] = useState("");

  async function load(currentToken: string) {
    const [applicationResponse, documentResponse] = await Promise.all([
      applicationApi.detail(currentToken, params.id),
      applicationApi.documents(currentToken, params.id),
    ]);
    setApplication(applicationResponse);
    setDocuments(documentResponse);
  }

  useEffect(() => {
    const currentToken = getToken();
    if (!currentToken) {
      router.push("/auth/login");
      return;
    }
    setTokenState(currentToken);
    load(currentToken).catch((err) =>
      setError(err instanceof Error ? err.message : "Could not load application"),
    );
  }, [params.id, router]);

  function onUploaded(document: DocumentMetadata) {
    setDocuments((current) => [document, ...current]);
    if (token) {
      load(token).catch(() => undefined);
    }
  }

  if (!application) {
    return (
      <PageShell>
        <p className="text-sm text-slate-600">{error || "Loading application..."}</p>
      </PageShell>
    );
  }

  return (
    <PageShell>
      <div className="grid gap-6">
        <div>
          <p className="text-sm font-semibold text-leaf">{serviceLabels[application.service_type]}</p>
          <h1 className="mt-1 text-3xl font-bold text-ink">{application.business_name}</h1>
          <p className="mt-2 text-sm text-slate-600">
            Status: <span className="font-semibold">{application.status.replaceAll("_", " ")}</span>
          </p>
        </div>

        {application.customer_clarification_message ? (
          <Card className="border-amber-200 bg-amber-50">
            <h2 className="font-bold text-ink">Clarification needed</h2>
            <p className="mt-2 text-sm leading-6 text-slate-700">
              {application.customer_clarification_message}
            </p>
          </Card>
        ) : null}

        <div className="grid gap-4 lg:grid-cols-[0.95fr_1.05fr]">
          <Card>
            <h2 className="text-xl font-bold text-ink">Missing documents</h2>
            {application.missing_required_documents.length ? (
              <ul className="mt-4 grid gap-2 text-sm text-slate-700">
                {application.missing_required_documents.map((documentType) => (
                  <li key={documentType} className="rounded-md bg-mist px-3 py-2">
                    {documentType.replaceAll("_", " ")}
                  </li>
                ))}
              </ul>
            ) : (
              <p className="mt-3 text-sm text-slate-600">
                All required documents are uploaded. Our team will review your application.
              </p>
            )}
          </Card>

          <Card>
            <h2 className="text-xl font-bold text-ink">Upload your documents</h2>
            <p className="mt-2 text-sm text-slate-600">Upload PDF/JPG/JPEG/PNG files up to 10MB.</p>
            <div className="mt-4">
              <DocumentUpload
                token={token}
                applicationId={params.id}
                missingDocuments={
                  application.missing_required_documents.length
                    ? application.missing_required_documents
                    : application.required_documents
                }
                onUploaded={onUploaded}
              />
            </div>
          </Card>
        </div>

        <Card>
          <h2 className="text-xl font-bold text-ink">Uploaded documents</h2>
          <div className="mt-4 grid gap-3">
            {documents.length === 0 ? <p className="text-sm text-slate-600">No documents uploaded yet.</p> : null}
            {documents.map((document) => (
              <div key={document.id} className="rounded-md border border-slate-200 p-3">
                <p className="font-semibold text-ink">{document.document_type.replaceAll("_", " ")}</p>
                <p className="mt-1 text-sm text-slate-600">{document.original_filename}</p>
                <p className="text-xs text-slate-500">
                  {(document.file_size / 1024).toFixed(1)} KB · {document.mime_type}
                </p>
                <p className="mt-1 text-xs font-semibold text-slate-600">
                  {document.requires_attention ? "Document requires attention" : `Document ${document.ai_processing_status}`}
                </p>
              </div>
            ))}
          </div>
        </Card>
      </div>
    </PageShell>
  );
}
