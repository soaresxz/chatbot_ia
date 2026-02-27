export const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"

export async function fetcher<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`)
  if (!res.ok) {
    throw new Error(`Erro ao buscar dados: ${res.status}`)
  }
  return res.json() as Promise<T>
}
