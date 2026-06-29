"use client";

import { useRouter } from "next/navigation";
import { FormEvent, useMemo, useState } from "react";
import { Card, Field, PageShell, inputClass } from "@/components/ui";
import { applicationApi } from "@/lib/api";
import { getToken } from "@/lib/auth";
import type { ApplicationPayload, ServiceType } from "@/types/api";

const services: { value: ServiceType; label: string }[] = [
  { value: "gst_registration", label: "GST Registration" },
  { value: "fssai_registration", label: "FSSAI Registration" },
  { value: "udyam_registration", label: "Udyam Registration" },
];

export default function NewApplicationPage() {
  const router = useRouter();
  const [serviceType, setServiceType] = useState<ServiceType>("gst_registration");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const serviceCopy = useMemo(() => {
    if (serviceType === "gst_registration") return "Start your GST registration";
    if (serviceType === "fssai_registration") return "Start your FSSAI registration";
    return "Start your Udyam registration";
  }, [serviceType]);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setLoading(true);
    const token = getToken();
    if (!token) {
      router.push("/auth/login");
      return;
    }
    const form = new FormData(event.currentTarget);
    const payload = Object.fromEntries(form.entries()) as Record<string, string>;
    const applicationPayload: ApplicationPayload = {
      ...payload,
      service_type: serviceType,
      title: serviceCopy,
      proprietor_name: payload.proprietor_name,
      business_name: payload.business_name,
      aadhaar_number: payload.aadhaar_number || null,
      bank_account_details: payload.bank_account_details || null,
      expected_turnover: payload.expected_turnover || null,
      nic_code: payload.nic_code || null,
      investment_amount: payload.investment_amount || null,
      turnover: payload.turnover || null,
    };
    try {
      const application = await applicationApi.create(token, applicationPayload);
      router.push(`/applications/${application.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not create application");
    } finally {
      setLoading(false);
    }
  }

  return (
    <PageShell>
      <div className="mx-auto max-w-3xl">
        <h1 className="text-3xl font-bold text-ink">{serviceCopy}</h1>
        <p className="mt-2 text-sm text-slate-600">
          Fill your details. We’ll contact you if anything is missing.
        </p>

        <Card className="mt-6">
          <form onSubmit={onSubmit} className="grid gap-5">
            <Field label="Service type">
              <select
                name="service_type"
                value={serviceType}
                onChange={(event) => setServiceType(event.target.value as ServiceType)}
                className={inputClass}
              >
                {services.map((service) => (
                  <option key={service.value} value={service.value}>
                    {service.label}
                  </option>
                ))}
              </select>
            </Field>

            <div className="grid gap-4 sm:grid-cols-2">
              <Field label="Applicant name">
                <input name="proprietor_name" required className={inputClass} />
              </Field>
              <Field label="Mobile">
                <input name="applicant_mobile" required className={inputClass} />
              </Field>
              <Field label="Email">
                <input name="applicant_email" type="email" required className={inputClass} />
              </Field>
              <Field label="PAN">
                <input name="pan_number" required className={inputClass} />
              </Field>
              <Field label="Aadhaar optional">
                <input name="aadhaar_number" className={inputClass} />
              </Field>
              <Field label="Business name">
                <input name="business_name" required className={inputClass} />
              </Field>
              <Field label="Business type">
                <input name="business_type" required className={inputClass} />
              </Field>
              <Field label="State">
                <input name="state" required className={inputClass} />
              </Field>
              <Field label="City">
                <input name="city" required className={inputClass} />
              </Field>
              <Field label="Pincode">
                <input name="pincode" required className={inputClass} />
              </Field>
            </div>

            <Field label="Business address">
              <textarea name="business_address" required className={`${inputClass} min-h-24`} />
            </Field>

            {serviceType === "gst_registration" ? (
              <div className="grid gap-4 sm:grid-cols-2">
                <Field label="Business constitution">
                  <input name="business_constitution" required className={inputClass} />
                </Field>
                <Field label="Nature of business">
                  <input name="nature_of_business" required className={inputClass} />
                </Field>
                <Field label="Principal place of business">
                  <input name="principal_place_of_business" required className={inputClass} />
                </Field>
                <Field label="Bank account details optional">
                  <input name="bank_account_details" className={inputClass} />
                </Field>
                <Field label="Expected turnover optional">
                  <input name="expected_turnover" className={inputClass} />
                </Field>
              </div>
            ) : null}

            {serviceType === "fssai_registration" ? (
              <div className="grid gap-4 sm:grid-cols-2">
                <Field label="Food business type">
                  <input name="food_business_type" required className={inputClass} />
                </Field>
                <Field label="Food category">
                  <input name="food_category" required className={inputClass} />
                </Field>
                <Field label="Annual turnover">
                  <input name="annual_turnover" required className={inputClass} />
                </Field>
                <Field label="Premises address">
                  <input name="premises_address" required className={inputClass} />
                </Field>
                <Field label="License type suggestion">
                  <input name="license_type_suggestion" required className={inputClass} />
                </Field>
                <input type="hidden" name="fssai_license_category" value="basic" />
              </div>
            ) : null}

            {serviceType === "udyam_registration" ? (
              <div className="grid gap-4 sm:grid-cols-2">
                <Field label="Enterprise name">
                  <input name="enterprise_name" required className={inputClass} />
                </Field>
                <Field label="Type of organisation">
                  <input name="type_of_organisation" required className={inputClass} />
                </Field>
                <Field label="Major activity">
                  <input name="major_activity" required className={inputClass} />
                </Field>
                <Field label="NIC code optional">
                  <input name="nic_code" className={inputClass} />
                </Field>
                <Field label="Investment amount optional">
                  <input name="investment_amount" className={inputClass} />
                </Field>
                <Field label="Turnover optional">
                  <input name="turnover" className={inputClass} />
                </Field>
                <input type="hidden" name="enterprise_type" value="micro" />
              </div>
            ) : null}

            {error ? <p className="rounded-md bg-red-50 p-3 text-sm text-red-700">{error}</p> : null}
            <button
              type="submit"
              disabled={loading}
              className="min-h-11 rounded-md bg-saffron px-4 py-2 text-sm font-semibold text-white disabled:opacity-60"
            >
              {loading ? "Creating..." : "Create application"}
            </button>
          </form>
        </Card>
      </div>
    </PageShell>
  );
}
