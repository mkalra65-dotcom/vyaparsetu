"use client";

import { FormEvent, useState } from "react";
import { documentApi } from "@/lib/api";
import { inputClass } from "@/components/ui";
import type { DocumentMetadata } from "@/types/api";

type Props = {
  token: string;
  applicationId: string;
  missingDocuments: string[];
  onUploaded: (document: DocumentMetadata) => void;
};

export function DocumentUpload({ token, applicationId, missingDocuments, onUploaded }: Props) {
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setMessage("");
    setError("");
    setLoading(true);
    const form = new FormData(event.currentTarget);
    const file = form.get("file");
    const documentType = String(form.get("document_type"));
    if (!(file instanceof File)) {
      setError("Please select a file");
      setLoading(false);
      return;
    }
    try {
      const uploaded = await documentApi.upload(token, applicationId, documentType, file);
      onUploaded(uploaded);
      setMessage("Upload successful. Our team will review your application.");
      event.currentTarget.reset();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <form onSubmit={onSubmit} className="grid gap-4">
      <label className="grid gap-1.5 text-sm font-medium text-slate-700">
        <span>Document type</span>
        <select name="document_type" required className={inputClass}>
          <option value="">Select document type</option>
          {missingDocuments.map((documentType) => (
            <option key={documentType} value={documentType}>
              {documentType.replaceAll("_", " ")}
            </option>
          ))}
        </select>
      </label>
      <label className="grid gap-1.5 text-sm font-medium text-slate-700">
        <span>Upload PDF/JPG/JPEG/PNG</span>
        <input
          name="file"
          type="file"
          accept=".pdf,.jpg,.jpeg,.png,application/pdf,image/jpeg,image/png"
          required
          className={inputClass}
        />
      </label>
      <p className="text-xs text-slate-500">Maximum file size: 10MB.</p>
      {message ? <p className="rounded-md bg-green-50 p-3 text-sm text-green-700">{message}</p> : null}
      {error ? <p className="rounded-md bg-red-50 p-3 text-sm text-red-700">{error}</p> : null}
      <button
        type="submit"
        disabled={loading}
        className="min-h-11 rounded-md bg-saffron px-4 py-2 text-sm font-semibold text-white disabled:opacity-60"
      >
        {loading ? "Uploading..." : "Upload your documents"}
      </button>
    </form>
  );
}
