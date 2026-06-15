import { useEffect, useState } from 'react';
import PackageCard from './PackageCard';
import { apiFetch } from '../lib/api';

function SkeletonCard() {
  return (
    <div
      className="animate-pulse rounded-2xl border-2 border-slate-100 bg-white p-6"
      aria-hidden="true"
    >
      <div className="mb-2 h-3 w-10 rounded bg-slate-100" />
      <div className="mb-4 h-6 w-24 rounded bg-slate-100" />
      <div className="mb-1 h-10 w-28 rounded bg-slate-100" />
      <div className="mb-5 h-14 w-full rounded bg-slate-100" />
      <div className="mb-5 h-5 w-32 rounded bg-slate-100" />
      <div className="h-11 w-full rounded-xl bg-slate-100" />
    </div>
  );
}

export default function PackageSelector({ selected, onSelect, headingId }) {
  const [packages, setPackages] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Fallback mirrors the real Cloud Package records so the form stays usable
  // even when the server is unreachable.
  const FALLBACK_PACKAGES = [
    {
      name: 'ZATCA_STARTER',
      title: 'ZATCA Starter',
      price: 0,
      users_limit: 5,
      description: 'ZATCA Phase 2 onboarding, B2B & B2C invoices, KSA Chart of Accounts, single warehouse.',
    },
    {
      name: 'ZATCA_RETAIL_POS',
      title: 'ZATCA Retail POS',
      price: 0,
      users_limit: 10,
      description: 'Everything in Starter plus POS setup (single outlet) and live ZATCA clearance.',
    },
    {
      name: 'ZATCA_COMPLETE_SME',
      title: 'ZATCA Complete SME',
      price: 0,
      users_limit: 0,
      description: 'Multi-warehouse, full accounting, VAT, Projects, CRM, and asset management.',
    },
  ];

  useEffect(() => {
    apiFetch(
      '/api/method/sowaan_cloud.sowaan_cloud.doctype.cloud_subscription.cloud_subscription.get_packages'
    )
      .then((r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.json();
      })
      .then((data) => {
        // Whitelisted methods return { message: <value> }
        const list = data?.message ?? [];
        if (list.length === 0) throw new Error('No packages returned');
        setPackages(list);
        if (!selected) onSelect(list[0].name);
      })
      .catch(() => {
        setPackages(FALLBACK_PACKAGES);
        if (!selected) onSelect(FALLBACK_PACKAGES[0].name);
        setError('Could not reach server — showing default packages.');
      })
      .finally(() => setLoading(false));
  }, []);

  const popularIdx = packages.length === 3 ? 1 : -1;

  return (
    <div>
      <div className="mb-12 text-center">
        <p className="mb-3 text-sm font-semibold uppercase tracking-widest text-blue-600">
          Pricing
        </p>
        <h2
          id={headingId}
          className="mb-3 text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl"
        >
          Simple, transparent pricing
        </h2>
        <p className="mx-auto max-w-xl text-slate-500">
          All plans include ZATCA Phase 2 e-invoicing. Upgrade or cancel anytime.
        </p>
      </div>

      {error && (
        <div
          role="status"
          className="mb-8 flex items-center gap-3 rounded-xl border border-amber-200 bg-amber-50 px-5 py-3.5 text-sm text-amber-700"
        >
          <svg
            className="h-5 w-5 shrink-0 text-amber-500"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={2}
            aria-hidden="true"
          >
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" />
          </svg>
          {error}
        </div>
      )}

      <div
        role="radiogroup"
        aria-label="Choose a plan"
        className="grid gap-6 sm:grid-cols-3"
      >
        {loading
          ? [0, 1, 2].map((i) => <SkeletonCard key={i} />)
          : packages.map((pkg, idx) => (
              <PackageCard
                key={pkg.name}
                pkg={pkg}
                selected={selected === pkg.name}
                onSelect={onSelect}
                popular={idx === popularIdx}
              />
            ))}
      </div>

      <p className="mt-6 text-center text-xs text-slate-400">
        All prices are in Saudi Riyal (SAR) and exclude VAT where applicable.
      </p>
    </div>
  );
}
