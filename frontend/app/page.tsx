import { ButtonLink, Card, PageShell } from "@/components/ui";
import { LeadForm } from "@/components/LeadForm";
import { PricingCards } from "@/components/PricingCards";

const services = [
  {
    title: "GST Registration",
    copy: "Start your GST registration with guided document collection and review.",
  },
  {
    title: "FSSAI Registration",
    copy: "Apply for food business registration with clear steps for MSME owners.",
  },
  {
    title: "Udyam Registration",
    copy: "Get started with Udyam registration for your enterprise details.",
  },
];

export default function HomePage() {
  return (
    <PageShell>
      <section className="grid gap-8 py-4 sm:grid-cols-[1.1fr_0.9fr] sm:items-center">
        <div className="grid gap-5">
          <p className="text-sm font-semibold uppercase tracking-wide text-leaf">Indian MSME support</p>
          <h1 className="text-4xl font-bold leading-tight text-ink sm:text-5xl">
            GST, FSSAI, and Udyam registration help for growing Indian businesses.
          </h1>
          <p className="max-w-2xl text-base leading-7 text-slate-650">
            VyaparSetu helps MSME owners collect documents, complete application details, and get
            human review before filing work begins. We’ll contact you if anything is missing.
          </p>
          <div className="flex flex-wrap gap-3">
            <ButtonLink href="/applications/new">Start Application</ButtonLink>
            <a href="#contact" className="inline-flex min-h-11 items-center rounded-md border border-slate-300 px-4 py-2 text-sm font-semibold">
              Talk to us
            </a>
          </div>
        </div>
        <div className="rounded-lg bg-mist p-5">
          <div className="grid gap-3">
            <div className="rounded-md bg-white p-4 shadow-soft">
              <p className="text-sm font-semibold text-slate-600">Current flow</p>
              <p className="mt-2 text-2xl font-bold text-ink">Documents reviewed by real people</p>
            </div>
            <div className="rounded-md bg-white p-4 shadow-soft">
              <p className="text-sm text-slate-700">Upload once, track status, respond to clarifications.</p>
            </div>
          </div>
        </div>
      </section>

      <section className="mt-10 grid gap-4 sm:grid-cols-3">
        {services.map((service) => (
          <Card key={service.title}>
            <h2 className="text-xl font-bold text-ink">{service.title}</h2>
            <p className="mt-3 text-sm leading-6 text-slate-600">{service.copy}</p>
          </Card>
        ))}
      </section>

      <section className="mt-12">
        <h2 className="text-2xl font-bold text-ink">Why businesses trust VyaparSetu</h2>
        <div className="mt-4 grid gap-4 sm:grid-cols-3">
          {["Human review before next steps", "Clear document checklists", "Simple status tracking"].map((item) => (
            <Card key={item}>
              <p className="font-semibold text-ink">{item}</p>
              <p className="mt-2 text-sm leading-6 text-slate-600">
                Built for small business owners who want a straightforward registration workflow.
              </p>
            </Card>
          ))}
        </div>
      </section>

      <section className="mt-12">
        <h2 className="text-2xl font-bold text-ink">How it works</h2>
        <div className="mt-4 grid gap-4 sm:grid-cols-4">
          {["Choose service", "Fill business details", "Upload documents", "Team reviews"].map((step, index) => (
            <Card key={step}>
              <p className="text-sm font-semibold text-leaf">Step {index + 1}</p>
              <p className="mt-2 font-bold text-ink">{step}</p>
            </Card>
          ))}
        </div>
      </section>

      <section className="mt-12">
        <h2 className="text-2xl font-bold text-ink">Pricing</h2>
        <p className="mt-2 text-sm text-slate-600">Pricing is configurable and shown from backend settings.</p>
        <div className="mt-4">
          <PricingCards />
        </div>
      </section>

      <section className="mt-12 grid gap-4 sm:grid-cols-2">
        <div>
          <h2 className="text-2xl font-bold text-ink">FAQ</h2>
          <div className="mt-4 grid gap-3">
            {[
              ["Do you submit to government portals automatically?", "No. VyaparSetu does not automate government portal submission."],
              ["Can I upload documents later?", "Yes. Your dashboard shows missing documents and upload status."],
              ["Which services are supported?", "GST Registration, FSSAI Registration, and Udyam Registration."],
            ].map(([question, answer]) => (
              <Card key={question}>
                <p className="font-semibold text-ink">{question}</p>
                <p className="mt-2 text-sm text-slate-600">{answer}</p>
              </Card>
            ))}
          </div>
        </div>
        <div id="contact">
          <Card>
            <h2 className="text-2xl font-bold text-ink">Contact us</h2>
            <p className="mt-2 text-sm text-slate-600">
              Leave your details and our team will help you choose the right registration.
            </p>
            <div className="mt-5">
              <LeadForm />
            </div>
          </Card>
        </div>
      </section>
    </PageShell>
  );
}
