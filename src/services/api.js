export async function apiCall(method, payload = {}) {
  const res = await fetch(`/api/call/${method}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify({ method, payload })
  });
  if (!res.ok) {
    throw new Error(`API error: ${res.statusText}`);
  }
  const data = await res.json();
  if (data && data.erro) {
    throw new Error(data.erro);
  }
  return data;
}

export async function listarAnalises() {
  const res = await fetch(`/api/listar_analises`, { credentials: 'include' });
  if (!res.ok) throw new Error("Erro ao listar analises");
  return res.json();
}
