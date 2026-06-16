import DOMPurify from 'dompurify';

export default function PackageCard({ pkg, selected, onSelect, popular }) {
  const hasPrice = pkg.price != null && pkg.price > 0;
  const usersLabel = pkg.users_limit > 0 ? `Up to ${pkg.users_limit} users` : 'Unlimited users';

  return (
    <button
      type="button"
      role="radio"
      aria-checked={selected}
      onClick={() => onSelect(pkg.name)}
      className={[
        'relative flex w-full flex-col rounded-2xl border-2 p-6 text-left transition-all duration-200',
        'focus-visible:outline-2 focus-visible:outline-blue-500 focus-visible:outline-offset-2',
        selected
          ? 'border-blue-500 bg-blue-50 shadow-lg shadow-blue-100'
          : popular
          ? 'border-violet-300 bg-white shadow-lg hover:border-violet-400 hover:shadow-xl'
          : 'border-slate-200 bg-white shadow-sm hover:border-slate-300 hover:shadow-md',
      ].join(' ')}
    >
      {popular && (
        <div className="absolute -top-4 left-1/2 -translate-x-1/2" aria-label="Most popular plan">
          <span className="rounded-full bg-gradient-to-r from-violet-500 to-blue-600 px-5 py-1.5 text-xs font-bold uppercase tracking-wide text-white shadow-md">
            Most Popular
          </span>
        </div>
      )}

      {selected && (
        <span
          aria-hidden="true"
          className="absolute right-5 top-5 flex h-6 w-6 items-center justify-center rounded-full bg-blue-600 text-white shadow"
        >
          <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
          </svg>
        </span>
      )}

      <div className="mb-1 text-xs font-semibold uppercase tracking-widest text-slate-400">
        Plan
      </div>

      <div className="mb-4 text-xl font-bold text-slate-900">
        {pkg.title || pkg.name}
      </div>

      {/* Price */}
      {hasPrice && (
        <div className="mb-1 flex items-baseline gap-1">
          <span className="text-4xl font-bold text-slate-900">
            {pkg.price.toLocaleString()}
          </span>
          <span className="text-lg font-semibold text-slate-500">SAR</span>
          <span className="text-sm text-slate-400">/mo</span>
        </div>
      )}

      {/* 15-day free trial — shown on every card */}
      <div className="mb-4 flex items-center gap-1.5 text-xs font-semibold text-emerald-600">
        <svg
          className="h-3.5 w-3.5 shrink-0"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          strokeWidth={2.5}
          aria-hidden="true"
        >
          <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
        </svg>
        15-day free trial included
      </div>

      {pkg.description && (
        <div
          className="package-desc mb-5 text-sm leading-relaxed text-slate-500 [&_b]:font-semibold [&_b]:text-slate-700 [&_ul]:mt-1.5 [&_ul]:space-y-1 [&_li]:flex [&_li]:items-start [&_li]:gap-1.5 [&_li]:before:mt-1 [&_li]:before:h-1.5 [&_li]:before:w-1.5 [&_li]:before:shrink-0 [&_li]:before:rounded-full [&_li]:before:bg-slate-300"
          dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(pkg.description) }}
        />
      )}

      {pkg.users_limit != null && (
        <div className="mb-5 flex items-center gap-2 text-sm text-slate-500">
          <svg
            className="h-4 w-4 shrink-0 text-slate-400"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={1.5}
            aria-hidden="true"
          >
            <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 6a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0zM4.501 20.118a7.5 7.5 0 0114.998 0A17.933 17.933 0 0112 21.75c-2.676 0-5.216-.584-7.499-1.632z" />
          </svg>
          {usersLabel}
        </div>
      )}

      <div
        className={[
          'mt-auto rounded-xl py-3 text-center text-sm font-bold tracking-wide transition-colors',
          selected
            ? 'bg-blue-600 text-white'
            : popular
            ? 'bg-violet-100 text-violet-700'
            : 'bg-slate-100 text-slate-700',
        ].join(' ')}
      >
        {selected ? '✓ Selected' : 'Choose Plan'}
      </div>
    </button>
  );
}
