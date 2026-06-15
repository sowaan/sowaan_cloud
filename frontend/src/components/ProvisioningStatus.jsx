import { useEffect, useRef, useState } from 'react';
import { apiFetch } from '../lib/api';

const STATUS_ENDPOINT =
  '/api/method/sowaan_cloud.sowaan_cloud.doctype.cloud_subscription.cloud_subscription.get_subscription_status';

// Order of provisioning_step values as set by sowaan_cloud.utils.provision
const STEP_ORDER = ['INIT', 'SITE_CREATED', 'APPS_INSTALLED', 'BOOTSTRAPPED', 'COMPLETED'];

const STEPS = [
  'Creating your site',
  'Installing applications',
  'Setting up your company',
  'Finalizing & going live',
];

const POLL_INTERVAL_MS = 4000;

function extractErrorMessage(body, status) {
  try {
    const msgs = JSON.parse(body?._server_messages || '[]');
    if (msgs[0]) return msgs[0]?.message || msgs[0];
  } catch (_) {}
  return body?.exception?.split('\n').at(-1) || body?.message || `HTTP ${status}`;
}

function StepIcon({ state }) {
  if (state === 'done') {
    return (
      <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-emerald-100 text-emerald-600">
        <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5} aria-hidden="true">
          <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
        </svg>
      </div>
    );
  }
  if (state === 'active') {
    return (
      <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-blue-100 text-blue-600">
        <svg className="h-4 w-4 animate-spin" viewBox="0 0 24 24" fill="none" aria-hidden="true">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" />
        </svg>
      </div>
    );
  }
  return <div className="h-8 w-8 shrink-0 rounded-full border-2 border-slate-200 bg-white" />;
}

export default function ProvisioningStatus({ subscriptionName, previewUrl }) {
  const [data, setData] = useState(null);
  const [pollError, setPollError] = useState(null);
  const timerRef = useRef(null);

  useEffect(() => {
    if (!subscriptionName) return;
    let cancelled = false;

    async function poll() {
      try {
        const res = await apiFetch(
          `${STATUS_ENDPOINT}?name=${encodeURIComponent(subscriptionName)}`
        );

        if (!res.ok) {
          const body = await res.json().catch(() => ({}));
          if (cancelled) return;
          setPollError(extractErrorMessage(body, res.status));
          // Back off entirely on a rate limit instead of hammering the
          // endpoint again every POLL_INTERVAL_MS.
          if (res.status !== 429) {
            timerRef.current = setTimeout(poll, POLL_INTERVAL_MS);
          }
          return;
        }

        const body = await res.json();
        if (cancelled) return;

        const result = body?.message ?? body;
        setData(result);
        setPollError(null);

        if (result.status === 'Provisioning' || result.status === 'Draft') {
          timerRef.current = setTimeout(poll, POLL_INTERVAL_MS);
        }
      } catch (err) {
        if (cancelled) return;
        setPollError(err.message || 'Unable to check status right now.');
        timerRef.current = setTimeout(poll, POLL_INTERVAL_MS);
      }
    }

    poll();

    return () => {
      cancelled = true;
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, [subscriptionName]);

  const status = data?.status;
  const completedCount = Math.max(0, STEP_ORDER.indexOf(data?.provisioning_step || 'INIT'));
  const siteUrl = data?.site_name
    ? `https://${data.site_name}`
    : previewUrl
      ? `https://${previewUrl}`
      : null;

  if (status === 'Active') {
    return (
      <div className="py-12 text-center">
        <div className="mx-auto mb-6 flex h-20 w-20 items-center justify-center rounded-full bg-emerald-100 ring-8 ring-emerald-50">
          <svg className="h-10 w-10 text-emerald-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2} aria-hidden="true">
            <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
          </svg>
        </div>
        <h3 className="mb-2 text-2xl font-bold text-slate-900">Your ERP is ready!</h3>
        <p className="mx-auto mb-6 max-w-xs text-slate-500">
          Your instance has been created and is live.
        </p>
        {siteUrl && (
          <a
            href={siteUrl}
            target="_blank"
            rel="noreferrer"
            className="cta-button inline-flex items-center gap-2 rounded-xl bg-blue-600 px-6 py-3.5 text-base font-bold text-white shadow-md shadow-blue-200 transition hover:bg-blue-700 hover:shadow-blue-300"
          >
            Open your ERP
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2} aria-hidden="true">
              <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 4.5 21 12m0 0-7.5 7.5M21 12H3" />
            </svg>
          </a>
        )}
        {siteUrl && (
          <p className="mx-auto mt-4 max-w-xs text-xs text-slate-400">
            If the link doesn&apos;t open right away, please wait a minute — your
            domain is still being activated.
          </p>
        )}
      </div>
    );
  }

  if (status === 'Failed') {
    return (
      <div className="py-12 text-center">
        <div className="mx-auto mb-6 flex h-20 w-20 items-center justify-center rounded-full bg-red-100 ring-8 ring-red-50">
          <svg className="h-10 w-10 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2} aria-hidden="true">
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
          </svg>
        </div>
        <h3 className="mb-2 text-2xl font-bold text-slate-900">Setup hit a snag</h3>
        <p className="mx-auto mb-4 max-w-sm text-slate-500">
          We couldn&apos;t finish setting up your instance. Our team has been notified — feel
          free to reach out to support and share the details below.
        </p>
        {data?.error && (
          <pre className="mx-auto max-w-md overflow-auto whitespace-pre-wrap rounded-xl border border-red-200 bg-red-50 p-4 text-left text-xs text-red-700">
            {data.error}
          </pre>
        )}
      </div>
    );
  }

  return (
    <div className="py-8">
      <div className="mx-auto mb-6 flex h-20 w-20 items-center justify-center rounded-full bg-blue-100 ring-8 ring-blue-50">
        <svg className="h-10 w-10 animate-spin text-blue-600" viewBox="0 0 24 24" fill="none" aria-hidden="true">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" />
        </svg>
      </div>
      <h3 className="mb-2 text-center text-2xl font-bold text-slate-900">
        Setting up your instance
      </h3>
      <p className="mb-8 text-center text-slate-500">
        This usually takes a few minutes. Feel free to keep this tab open.
      </p>

      <ol className="space-y-4">
        {STEPS.map((label, i) => {
          const state = i < completedCount ? 'done' : i === completedCount ? 'active' : 'pending';
          return (
            <li key={label} className="flex items-center gap-3">
              <StepIcon state={state} />
              <span className={state === 'pending' ? 'text-slate-400' : 'text-slate-900'}>
                {label}
              </span>
            </li>
          );
        })}
      </ol>

      {pollError && <p className="mt-6 text-center text-xs text-slate-400">{pollError}</p>}
    </div>
  );
}
