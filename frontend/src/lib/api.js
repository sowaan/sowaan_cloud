const BASE = import.meta.env.VITE_API_BASE_URL || '';

const UNSAFE_METHODS = new Set(['POST', 'PUT', 'PATCH', 'DELETE']);

function getCsrfToken() {
  return window.frappe?.csrf_token ?? null;
}

export async function apiFetch(path, options = {}) {
  const { headers: extraHeaders, ...rest } = options;
  const method = (options.method || 'GET').toUpperCase();
  const csrfToken = UNSAFE_METHODS.has(method) ? getCsrfToken() : null;

  return fetch(`${BASE}${path}`, {
    ...rest,
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
      ...(csrfToken ? { 'X-Frappe-CSRF-Token': csrfToken } : {}),
      ...extraHeaders,
    },
  });
}
