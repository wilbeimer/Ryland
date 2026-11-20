import { vi } from 'vitest'

type Json = unknown

type RouteHandler = (url: URL) => { status?: number; body: Json } | null

export function mockApi(routes: RouteHandler[]): void {
  vi.stubGlobal(
    'fetch',
    vi.fn(async (input: RequestInfo | URL) => {
      const url =
        typeof input === 'string'
          ? new URL(input, 'http://localhost')
          : input instanceof URL
            ? input
            : new URL(input.url, 'http://localhost')

      for (const route of routes) {
        const result = route(url)
        if (result) {
          return new Response(JSON.stringify(result.body), {
            status: result.status ?? 200,
            headers: { 'Content-Type': 'application/json' },
          })
        }
      }

      return new Response(JSON.stringify({ detail: `No mock for ${url.pathname}` }), {
        status: 404,
        headers: { 'Content-Type': 'application/json' },
      })
    }),
  )
}
