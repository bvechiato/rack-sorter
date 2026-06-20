const API_HOST = window.location.origin;

async function handleResponse(res: Response): Promise<any> {
  if (!res.ok) {
    if (res.status === 0 || res.statusText === 'Unknown Error') {
      throw new Error('Backend server not running. Start it with: python -m uvicorn main:app --host 0.0.0.0 --port 8000');
    }
    const error = await res.json().catch(() => ({}));
    throw new Error(error.message || `API error: ${res.status}`);
  }
  return res.json();
}

export async function analyzeFile(file: File): Promise<any> {
  const formData = new FormData();
  formData.append('file', file as Blob);
  try {
    const res = await fetch(`${API_HOST}/analyze`, { method: 'POST', body: formData });
    return await handleResponse(res);
  } catch (err: any) {
    throw new Error(err?.message || 'Failed to analyze image');
  }
}

export async function fetchInitial(formData: FormData): Promise<any> {
  try {
    const res = await fetch(`${API_HOST}/fetch_initial`, { method: 'POST', body: formData });
    return await handleResponse(res);
  } catch (err: any) {
    throw new Error(err?.message || 'Failed to fetch items');
  }
}

export async function rerank(formData: FormData): Promise<any> {
  try {
    const res = await fetch(`${API_HOST}/rerank`, { method: 'POST', body: formData });
    return await handleResponse(res);
  } catch (err: any) {
    throw new Error(err?.message || 'Failed to rerank items');
  }
}

export default { analyzeFile, fetchInitial, rerank };
