"use client";

import { useEffect, useState } from "react";
import { Card } from "@/components/ui";
import { publicApi } from "@/lib/api";
import type { Pricing } from "@/types/api";

const fallback = {
  gst_registration: { label: "GST Registration", price: "Configured on backend" },
  fssai_registration: { label: "FSSAI Registration", price: "Configured on backend" },
  udyam_registration: { label: "Udyam Registration", price: "Configured on backend" },
} as Pricing;

export function PricingCards() {
  const [pricing, setPricing] = useState<Pricing>(fallback);

  useEffect(() => {
    publicApi.pricing().then(setPricing).catch(() => undefined);
  }, []);

  return (
    <div className="grid gap-4 sm:grid-cols-3">
      {Object.entries(pricing).map(([key, item]) => (
        <Card key={key}>
          <h3 className="text-lg font-bold text-ink">{item.label}</h3>
          <p className="mt-3 text-2xl font-bold text-leaf">{item.price}</p>
          <p className="mt-3 text-sm leading-6 text-slate-600">
            Includes guided details, document checklist, review, and customer support.
          </p>
        </Card>
      ))}
    </div>
  );
}
