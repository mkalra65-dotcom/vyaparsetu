"use client";

import { FormEvent, useState } from "react";
import { Field, inputClass } from "@/components/ui";
import { publicApi } from "@/lib/api";

export function LeadForm() {
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setMessage("");
    setError("");
    const form = new FormData(event.currentTarget);
    try {
      await publicApi.createLead({
        name: String(form.get("name")),
        mobile: String(form.get("mobile")),
        email: String(form.get("email") || "") || undefined,
        service_interest: String(form.get("service_interest")),
        message: String(form.get("message") || "") || undefined,
      });
      setMessage("Thanks. Our team will contact you shortly.");
      event.currentTarget.reset();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not submit your enquiry");
    }
  }

  return (
    <form onSubmit={onSubmit} className="grid gap-4">
      <Field label="Name">
        <input name="name" required className={inputClass} />
      </Field>
      <Field label="Mobile">
        <input name="mobile" required className={inputClass} />
      </Field>
      <Field label="Email">
        <input name="email" type="email" className={inputClass} />
      </Field>
      <Field label="Service">
        <select name="service_interest" required className={inputClass}>
          <option value="gst_registration">GST Registration</option>
          <option value="fssai_registration">FSSAI Registration</option>
          <option value="udyam_registration">Udyam Registration</option>
        </select>
      </Field>
      <Field label="Message">
        <textarea name="message" className={`${inputClass} min-h-24`} />
      </Field>
      {message ? <p className="rounded-md bg-green-50 p-3 text-sm text-green-700">{message}</p> : null}
      {error ? <p className="rounded-md bg-red-50 p-3 text-sm text-red-700">{error}</p> : null}
      <button className="min-h-11 rounded-md bg-saffron px-4 py-2 text-sm font-semibold text-white">
        Request a callback
      </button>
    </form>
  );
}
