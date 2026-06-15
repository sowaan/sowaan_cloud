import { useState } from 'react';
import { apiFetch } from '../lib/api';
import ProvisioningStatus from './ProvisioningStatus';

function Field({ id, label, required, hint, error, children }) {
  return (
    <div>
      <label htmlFor={id} className="mb-1.5 block text-sm font-medium text-slate-700">
        {label}
        {required && (
          <span className="ml-1 text-red-500" aria-hidden="true">*</span>
        )}
      </label>
      {children}
      {hint && !error && (
        <p id={`${id}-hint`} className="mt-1.5 text-xs text-slate-400">{hint}</p>
      )}
      {error && (
        <p id={`${id}-error`} role="alert" className="mt-1.5 flex items-center gap-1.5 text-xs text-red-600">
          <svg className="h-3.5 w-3.5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2} aria-hidden="true">
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
          </svg>
          {error}
        </p>
      )}
    </div>
  );
}

function inputCls(hasError) {
  return [
    'w-full rounded-xl border bg-white px-4 py-3.5 text-slate-900 placeholder-slate-400',
    'outline-none transition-all duration-150',
    'focus:ring-2 disabled:cursor-not-allowed disabled:opacity-60',
    hasError
      ? 'border-red-300 focus:border-red-500 focus:ring-red-500/20'
      : 'border-slate-300 focus:border-blue-500 focus:ring-blue-500/20',
  ].join(' ');
}

function validate(form) {
  return {
    company_name:  !form.company_name.trim()  ? 'Company name is required'         : null,
    abbr:          !form.abbr.trim()           ? 'Abbreviation is required'          : null,
    instance_name: !form.instance_name.trim()  ? 'Instance name is required'         : null,
    user_email:
      !form.user_email.trim() || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.user_email)
        ? 'Enter a valid email address' : null,
    user_password:
      !form.user_password ? 'Password is required' :
      form.user_password.length < 8 ? 'Password must be at least 8 characters' : null,
  };
}

export default function SignupForm({ selectedPackage }) {
  const [form, setForm] = useState({
    company_name: '',
    abbr: '',
    instance_name: '',
    user_email: '',
    user_password: '',
    hp: '',
  });
  const [touched, setTouched] = useState({});
  const [showPassword, setShowPassword] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [success, setSuccess] = useState(false);
  const [serverError, setServerError] = useState(null);
  const [subscriptionName, setSubscriptionName] = useState(null);

  const allErrors = validate(form);
  const errors = Object.fromEntries(
    Object.entries(allErrors).map(([k, v]) => [k, touched[k] ? v : null])
  );

  function set(field, value) {
    setForm((f) => ({ ...f, [field]: value }));
  }
  function touch(field) {
    setTouched((t) => ({ ...t, [field]: true }));
  }
  function handleAbbrChange(e) {
    set('abbr', e.target.value.toUpperCase().replace(/[^A-Z0-9]/g, '').slice(0, 5));
  }
  function handleInstanceChange(e) {
    set('instance_name', e.target.value.toLowerCase().replace(/[^a-z0-9-]/g, ''));
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setTouched({
      company_name: true, abbr: true, instance_name: true,
      user_email: true, user_password: true,
    });

    if (Object.values(allErrors).some(Boolean)) return;

    setServerError(null);
    setSubmitting(true);

    try {
      const res = await apiFetch(
        '/api/method/sowaan_cloud.sowaan_cloud.doctype.cloud_subscription.cloud_subscription.create_subscription',
        {
          method: 'POST',
          body: JSON.stringify({
            company_name:  form.company_name,
            abbr:          form.abbr,
            instance_name: form.instance_name,
            user_email:    form.user_email,
            user_password: form.user_password,
            selected_package: selectedPackage,
            country: 'Saudi Arabia',
            hp: form.hp,
          }),
        }
      );

      const body = await res.json().catch(() => ({}));

      if (!res.ok) {
        let serverMsg = null;
        try {
          const msgs = JSON.parse(body?._server_messages || '[]');
          serverMsg = msgs[0]?.message || msgs[0];
        } catch (_) {}
        throw new Error(
          serverMsg ||
          body?.exception?.split('\n').at(-1) ||
          body?.message ||
          `HTTP ${res.status}`
        );
      }

      const result = body?.message ?? body;
      setSubscriptionName(result?.name ?? null);
      setSuccess(true);
    } catch (err) {
      setServerError(err.message || 'Something went wrong. Please try again.');
    } finally {
      setSubmitting(false);
    }
  }

  if (success) {
    return (
      <ProvisioningStatus
        subscriptionName={subscriptionName}
        previewUrl={form.instance_name ? `${form.instance_name}.sowaan.cloud` : null}
      />
    );
  }

  return (
    <form onSubmit={handleSubmit} noValidate className="space-y-5">
      <p className="sr-only">Fields marked with * are required</p>

      {/* Honeypot */}
      <div aria-hidden="true" style={{ position: 'absolute', left: '-9999px', width: '1px', height: '1px', overflow: 'hidden' }}>
        <label htmlFor="website">Website</label>
        <input id="website" type="text" name="website" tabIndex={-1} autoComplete="off" value={form.hp} onChange={(e) => set('hp', e.target.value)} />
      </div>

      <Field id="company_name" label="Company Name" required error={errors.company_name}>
        <input
          id="company_name" type="text" required autoComplete="organization"
          placeholder="Acme Arabia Co." value={form.company_name}
          onChange={(e) => set('company_name', e.target.value)} onBlur={() => touch('company_name')}
          aria-describedby={errors.company_name ? 'company_name-error' : undefined}
          aria-invalid={!!errors.company_name} className={inputCls(errors.company_name)}
        />
      </Field>

      <Field id="abbr" label="Company Abbreviation" required hint="Up to 5 uppercase characters — used inside ERPNext" error={errors.abbr}>
        <input
          id="abbr" type="text" required maxLength={5} autoComplete="off"
          placeholder="ACME" value={form.abbr}
          onChange={handleAbbrChange} onBlur={() => touch('abbr')}
          aria-describedby={errors.abbr ? 'abbr-error' : 'abbr-hint'}
          aria-invalid={!!errors.abbr} className={`${inputCls(errors.abbr)} font-mono tracking-[0.25em]`}
        />
      </Field>

      <Field id="instance_name" label="Instance Name" required hint="Lowercase letters, numbers and hyphens only" error={errors.instance_name}>
        <input
          id="instance_name" type="text" required autoComplete="off"
          placeholder="acme-arabia" value={form.instance_name}
          onChange={handleInstanceChange} onBlur={() => touch('instance_name')}
          aria-describedby={errors.instance_name ? 'instance_name-error' : form.instance_name ? 'instance_name-preview' : 'instance_name-hint'}
          aria-invalid={!!errors.instance_name} className={inputCls(errors.instance_name)}
        />
        {form.instance_name && !errors.instance_name && (
          <p id="instance_name-preview" className="mt-2 flex items-center gap-2 rounded-lg border border-blue-200 bg-blue-50 px-3 py-2 font-mono text-xs text-blue-700">
            <svg className="h-3.5 w-3.5 shrink-0 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2} aria-hidden="true">
              <path strokeLinecap="round" strokeLinejoin="round" d="M13.19 8.688a4.5 4.5 0 011.242 7.244l-4.5 4.5a4.5 4.5 0 01-6.364-6.364l1.757-1.757m13.35-.622 1.757-1.757a4.5 4.5 0 00-6.364-6.364l-4.5 4.5a4.5 4.5 0 001.242 7.244" />
            </svg>
            {form.instance_name}.sowaan.cloud
          </p>
        )}
      </Field>

      <Field id="user_email" label="Email Address" required error={errors.user_email}>
        <input
          id="user_email" type="email" required autoComplete="email"
          placeholder="admin@acme.com" value={form.user_email}
          onChange={(e) => set('user_email', e.target.value)} onBlur={() => touch('user_email')}
          aria-describedby={errors.user_email ? 'user_email-error' : undefined}
          aria-invalid={!!errors.user_email} className={inputCls(errors.user_email)}
        />
      </Field>

      <Field id="user_password" label="Password" required hint="Minimum 8 characters" error={errors.user_password}>
        <div className="relative">
          <input
            id="user_password"
            type={showPassword ? 'text' : 'password'}
            required
            autoComplete="new-password"
            placeholder="••••••••"
            value={form.user_password}
            onChange={(e) => set('user_password', e.target.value)}
            onBlur={() => touch('user_password')}
            aria-describedby={errors.user_password ? 'user_password-error' : 'user_password-hint'}
            aria-invalid={!!errors.user_password}
            className={`${inputCls(errors.user_password)} pr-12`}
          />
          <button
            type="button"
            aria-label={showPassword ? 'Hide password' : 'Show password'}
            onClick={() => setShowPassword((v) => !v)}
            className="absolute right-3 top-1/2 -translate-y-1/2 rounded p-1 text-slate-400 transition hover:text-slate-600 focus-visible:outline-2 focus-visible:outline-blue-500"
          >
            {showPassword ? (
              <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.75}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M3.98 8.223A10.477 10.477 0 001.934 12C3.226 16.338 7.244 19.5 12 19.5c.993 0 1.953-.138 2.863-.395M6.228 6.228A10.45 10.45 0 0112 4.5c4.756 0 8.773 3.162 10.065 7.498a10.523 10.523 0 01-4.293 5.774M6.228 6.228L3 3m3.228 3.228l3.65 3.65m7.894 7.894L21 21m-3.228-3.228l-3.65-3.65m0 0a3 3 0 10-4.243-4.243m4.242 4.242L9.88 9.88" />
              </svg>
            ) : (
              <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.75}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M2.036 12.322a1.012 1.012 0 010-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178z" />
                <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
            )}
          </button>
        </div>
      </Field>

      {serverError && (
        <div role="alert" className="flex items-start gap-3 rounded-xl border border-red-200 bg-red-50 px-4 py-3.5 text-sm text-red-700">
          <svg className="mt-0.5 h-4 w-4 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2} aria-hidden="true">
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
          </svg>
          {serverError}
        </div>
      )}

      <button
        type="submit"
        disabled={submitting}
        className="flex w-full items-center justify-center gap-2 rounded-xl bg-blue-600 px-6 py-4 text-base font-bold text-white shadow-md shadow-blue-200 transition hover:bg-blue-700 hover:shadow-blue-300 active:scale-[0.99] disabled:cursor-not-allowed disabled:opacity-60 focus-visible:outline-2 focus-visible:outline-blue-500 focus-visible:outline-offset-2"
      >
        {submitting ? (
          <>
            <svg className="h-5 w-5 animate-spin" viewBox="0 0 24 24" fill="none" aria-hidden="true">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" />
            </svg>
            Setting up your instance…
          </>
        ) : (
          <>
            Start Free Trial
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2} aria-hidden="true">
              <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 4.5 21 12m0 0-7.5 7.5M21 12H3" />
            </svg>
          </>
        )}
      </button>

      <p className="text-center text-xs text-slate-400">
        By submitting you agree to our{' '}
        <a href="#" className="text-slate-600 underline underline-offset-2 hover:text-blue-600">Terms of Service</a>
        {' '}and{' '}
        <a href="#" className="text-slate-600 underline underline-offset-2 hover:text-blue-600">Privacy Policy</a>.
      </p>
    </form>
  );
}
