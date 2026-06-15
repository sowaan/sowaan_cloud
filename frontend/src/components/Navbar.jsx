import { useState } from 'react';

export default function Navbar() {
  const [menuOpen, setMenuOpen] = useState(false);

  return (
    <header>
      <nav
        className="sticky top-0 z-50 border-b border-slate-200/80 bg-white/95 shadow-sm backdrop-blur-md"
        aria-label="Main navigation"
      >
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
          {/* Logo */}
          <a href="#" className="flex items-center gap-3 focus-visible:outline-2 focus-visible:outline-blue-500 focus-visible:outline-offset-2 rounded-lg">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-blue-600 to-blue-700 font-bold text-white shadow-md shadow-blue-200">
              S
            </div>
            <span className="text-lg font-semibold tracking-tight text-slate-900">
              Sowaan <span className="text-blue-600">Cloud</span>
            </span>
          </a>

          {/* Desktop links */}
          <div className="hidden items-center gap-8 md:flex">
            <a href="#features" className="text-sm font-medium text-slate-500 transition hover:text-slate-900">
              Features
            </a>
            <a href="#pricing" className="text-sm font-medium text-slate-500 transition hover:text-slate-900">
              Pricing
            </a>
            <a href="#signup" className="text-sm font-medium text-slate-500 transition hover:text-slate-900">
              Support
            </a>
          </div>

          <div className="flex items-center gap-3">
            <a
              href="#signup"
              className="hidden rounded-lg bg-blue-600 px-5 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:bg-blue-700 focus-visible:outline-2 focus-visible:outline-blue-500 focus-visible:outline-offset-2 md:block"
            >
              Start Free Trial
            </a>

            {/* Hamburger */}
            <button
              type="button"
              aria-label={menuOpen ? 'Close menu' : 'Open menu'}
              aria-expanded={menuOpen}
              aria-controls="mobile-menu"
              onClick={() => setMenuOpen((o) => !o)}
              className="flex h-10 w-10 items-center justify-center rounded-lg border border-slate-200 text-slate-600 transition hover:bg-slate-100 focus-visible:outline-2 focus-visible:outline-blue-500 md:hidden"
            >
              {menuOpen ? (
                <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                </svg>
              ) : (
                <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M4 6h16M4 12h16M4 18h16" />
                </svg>
              )}
            </button>
          </div>
        </div>

        {/* Mobile menu */}
        {menuOpen && (
          <div
            id="mobile-menu"
            className="border-t border-slate-100 bg-white px-6 py-5 md:hidden"
          >
            <div className="flex flex-col gap-4">
              <a
                href="#features"
                onClick={() => setMenuOpen(false)}
                className="text-sm font-medium text-slate-700 transition hover:text-blue-600"
              >
                Features
              </a>
              <a
                href="#pricing"
                onClick={() => setMenuOpen(false)}
                className="text-sm font-medium text-slate-700 transition hover:text-blue-600"
              >
                Pricing
              </a>
              <a
                href="#signup"
                onClick={() => setMenuOpen(false)}
                className="text-sm font-medium text-slate-700 transition hover:text-blue-600"
              >
                Support
              </a>
              <a
                href="#signup"
                onClick={() => setMenuOpen(false)}
                className="rounded-lg bg-blue-600 px-4 py-3 text-center text-sm font-semibold text-white transition hover:bg-blue-700"
              >
                Start Free Trial
              </a>
            </div>
          </div>
        )}
      </nav>
    </header>
  );
}
