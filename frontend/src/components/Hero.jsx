const features = [
  {
    icon: (
      <svg className="h-6 w-6 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 13.5l10.5-11.25L12 10.5h8.25L9.75 21.75 12 13.5H3.75z" />
      </svg>
    ),
    title: 'Live in 5 Minutes',
    desc: 'Your ERPNext instance is provisioned instantly — no manual setup, no DevOps required.',
  },
  {
    icon: (
      <svg className="h-6 w-6 text-emerald-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z" />
      </svg>
    ),
    title: 'ZATCA Phase 2 Certified',
    desc: 'Full e-invoicing compliance built in from day one. Audit-ready and always up to date.',
  },
  {
    icon: (
      <svg className="h-6 w-6 text-violet-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 12l8.954-8.955c.44-.439 1.152-.439 1.591 0L21.75 12M4.5 9.75v10.125c0 .621.504 1.125 1.125 1.125H9.75v-4.875c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125V21h4.125c.621 0 1.125-.504 1.125-1.125V9.75M8.25 21h8.25" />
      </svg>
    ),
    title: 'Saudi Arabia Hosted',
    desc: 'Data sovereignty guaranteed. Your data stays within Saudi Arabia — always.',
  },
];

export default function Hero() {
  return (
    <>
      {/* ── Dark hero ── */}
      <section
        id="hero"
        aria-label="Sowaan Cloud — ERP for Saudi Business"
        className="relative overflow-hidden bg-gradient-to-br from-slate-900 via-blue-950 to-slate-900 py-24 text-center sm:py-32"
      >
        {/* Decorative blobs */}
        <div className="pointer-events-none absolute inset-0 overflow-hidden" aria-hidden="true">
          <div className="absolute -top-40 left-1/2 h-[600px] w-[600px] -translate-x-1/2 rounded-full bg-blue-600/10 blur-3xl" />
          <div className="absolute -bottom-20 left-1/4 h-[400px] w-[400px] rounded-full bg-indigo-500/8 blur-3xl" />
          <div className="absolute top-1/3 right-0 h-[300px] w-[300px] rounded-full bg-cyan-500/8 blur-3xl" />
        </div>

        <div className="relative mx-auto max-w-3xl px-6">
          {/* ZATCA badge */}
          <div className="mb-8 inline-flex items-center gap-2.5 rounded-full border border-emerald-400/30 bg-emerald-500/10 px-5 py-2 text-sm font-semibold text-emerald-400">
            <span className="h-2 w-2 animate-pulse rounded-full bg-emerald-400" aria-hidden="true" />
            ZATCA Phase 2 Certified &nbsp;·&nbsp; مرحلة 2 فاتورة
          </div>

          <h1 className="mb-6 text-4xl font-bold leading-[1.1] tracking-tight text-white sm:text-5xl lg:text-6xl">
            The Cloud ERP Built
            <br />
            <span className="bg-gradient-to-r from-blue-400 to-cyan-400 bg-clip-text text-transparent">
              for Saudi Business
            </span>
          </h1>

          <p className="mb-10 text-lg leading-relaxed text-slate-300">
            Launch a fully compliant ERPNext instance in minutes.
            <br className="hidden sm:block" />
            ZATCA e-invoicing, VAT-ready, hosted in Saudi Arabia.
          </p>

          <div className="flex flex-col items-center justify-center gap-4 sm:flex-row">
            <a
              href="#signup"
              className="inline-flex items-center gap-2 rounded-xl bg-blue-600 px-8 py-4 text-base font-semibold text-white shadow-lg shadow-blue-900/40 transition hover:bg-blue-500 focus-visible:outline-2 focus-visible:outline-white focus-visible:outline-offset-2"
            >
              Start Free Trial
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 4.5 21 12m0 0-7.5 7.5M21 12H3" />
              </svg>
            </a>
            <a
              href="#pricing"
              className="inline-flex items-center gap-2 rounded-xl border border-white/20 bg-white/5 px-8 py-4 text-base font-semibold text-white transition hover:bg-white/10 focus-visible:outline-2 focus-visible:outline-white focus-visible:outline-offset-2"
            >
              View Plans
            </a>
          </div>

          {/* Trust strip */}
          <div className="mt-12 flex flex-wrap items-center justify-center gap-x-6 gap-y-3 text-sm text-slate-400">
            {[
              'Saudi Arabia hosted',
              'No credit card required',
              'Live in under 5 minutes',
              'Full ZATCA compliance',
            ].map((item) => (
              <span key={item} className="flex items-center gap-2">
                <svg
                  className="h-4 w-4 shrink-0 text-emerald-400"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  strokeWidth={2.5}
                  aria-hidden="true"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                </svg>
                {item}
              </span>
            ))}
          </div>
        </div>
      </section>

      {/* ── Feature strip ── */}
      <section id="features" className="border-b border-slate-200 bg-white py-16">
        <div className="mx-auto max-w-5xl px-6">
          <div className="grid gap-10 sm:grid-cols-3">
            {features.map(({ icon, title, desc }) => (
              <div key={title} className="flex flex-col items-start gap-3">
                <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-slate-50 ring-1 ring-slate-200">
                  {icon}
                </div>
                <h3 className="text-base font-semibold text-slate-900">{title}</h3>
                <p className="text-sm leading-relaxed text-slate-500">{desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>
    </>
  );
}
