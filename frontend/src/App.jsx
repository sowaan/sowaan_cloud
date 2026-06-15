import { useState } from 'react';
import Navbar from './components/Navbar';
import Hero from './components/Hero';
import PackageSelector from './components/PackageSelector';
import SignupForm from './components/SignupForm';

export default function App() {
  const [selectedPackage, setSelectedPackage] = useState(null);

  return (
    <div className="min-h-screen">
      <Navbar />

      <main>
        <Hero />

        <section
          id="pricing"
          className="bg-slate-50 py-20"
          aria-labelledby="pricing-heading"
        >
          <div className="mx-auto max-w-5xl px-6">
            <PackageSelector
              selected={selectedPackage}
              onSelect={setSelectedPackage}
              headingId="pricing-heading"
            />
          </div>
        </section>

        <section
          id="signup"
          className="bg-white py-20"
          aria-labelledby="signup-heading"
        >
          <div className="mx-auto max-w-lg px-6">
            <div className="mb-10 text-center">
              <p className="mb-2 text-sm font-semibold uppercase tracking-widest text-blue-600">
                Get Started
              </p>
              <h2
                id="signup-heading"
                className="mb-3 text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl"
              >
                Create your account
              </h2>
              <p className="text-slate-500">
                Get started in under 2 minutes. No credit card required.
              </p>
            </div>

            <div className="rounded-2xl border border-slate-200 bg-white p-8 shadow-xl shadow-slate-100">
              <SignupForm selectedPackage={selectedPackage} />
            </div>
          </div>
        </section>
      </main>

      <footer className="border-t border-slate-800 bg-slate-900 py-12">
        <div className="mx-auto max-w-5xl px-6">
          <div className="flex flex-col items-center justify-between gap-6 sm:flex-row">
            <div className="flex items-center gap-3">
              <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-blue-600 font-bold text-white shadow-md">
                S
              </div>
              <div>
                <div className="text-sm font-semibold text-white">Sowaan Cloud</div>
                <div className="text-xs text-slate-400">ZATCA Phase 2 Certified ERP</div>
              </div>
            </div>

            <p className="text-sm text-slate-500">
              © {new Date().getFullYear()} Sowaan Cloud. All rights reserved.
            </p>

            <nav aria-label="Footer links" className="flex gap-6 text-sm">
              <a href="#" className="text-slate-400 transition hover:text-white">Privacy</a>
              <a href="#" className="text-slate-400 transition hover:text-white">Terms</a>
              <a href="#" className="text-slate-400 transition hover:text-white">Support</a>
            </nav>
          </div>
        </div>
      </footer>
    </div>
  );
}
