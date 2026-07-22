let csrfToken

async function secureHeaders(method) {
  if (!['POST', 'PUT', 'PATCH', 'DELETE'].includes(method?.toUpperCase())) return {}
  if (!csrfToken) {
    const response = await fetch('/api/auth/csrf', { credentials: 'include' })
    const body = await response.json()
    csrfToken = body.csrfToken
  }
  return { 'X-CSRFToken': csrfToken }
}

export async function api(path, options = {}) {
  const securityHeaders = await secureHeaders(options.method)
  const contentHeaders = options.body instanceof FormData ? {} : { 'Content-Type': 'application/json' }
  const response = await fetch(`/api${path}`, {
    credentials: 'include',
    headers: { ...contentHeaders, ...securityHeaders, ...options.headers },
    ...options,
  })
  if (response.status === 204) return null
  const body = await response.json()
  if (!response.ok) throw new Error(body.message || 'Something went wrong.')
  return body
}

export function euro(cents) {
  return new Intl.NumberFormat('en-IE', { style: 'currency', currency: 'EUR' }).format(cents / 100)
}

export function eventDate(value) {
  return new Intl.DateTimeFormat('en-IE', { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(value))
}
