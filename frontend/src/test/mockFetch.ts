import { vi } from 'vitest'

type Json = unknown

type RouteResult = {
  status?: number
  body?: Json
  /** When true, respond with an empty body (e.g. 204). */
  empty?: boolean
}

type RouteHandler = (
  url: URL,
  init?: RequestInit,
) => RouteResult | null

export function mockApi(routes: RouteHandler[]): void {
  vi.stubGlobal(
    'fetch',
    vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url =
        typeof input === 'string'
          ? new URL(input, 'http://localhost')
          : input instanceof URL
            ? input
            : new URL(input.url, 'http://localhost')

      for (const route of routes) {
        const result = route(url, init)
        if (result) {
          if (result.empty) {
            return new Response(null, { status: result.status ?? 204 })
          }
          return new Response(JSON.stringify(result.body ?? null), {
            status: result.status ?? 200,
            headers: { 'Content-Type': 'application/json' },
          })
        }
      }

      return new Response(
        JSON.stringify({ detail: `No mock for ${url.pathname}` }),
        {
          status: 404,
          headers: { 'Content-Type': 'application/json' },
        },
      )
    }),
  )
}
