import { components } from './types/api'; 

type AnalyseAnchorImageResponse = components['schemas']['AnalyseAnchorImageResponse'];
type FetchInitialRequest = components['schemas']['FetchInitialRequest'];
type FetchInitialResponse = components['schemas']['FetchInitialResponse'];
type RerankRequest = components['schemas']['RerankRequest'];
type BatchRerankRequest = components['schemas']['BatchRerankRequest'];
type TraitProfileResponse = components['schemas']['TraitProfileResponse'];

const API_HOST = window.location.origin;

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    if (res.status === 0) {
      throw new Error('Backend server not running.');
    }
    const error = await res.json().catch(() => ({}));
    throw new Error(error.message || `API error: ${res.status}`);
  }
  return res.json() as Promise<T>;
}

export async function analyzeFile(file: File): Promise<AnalyseAnchorImageResponse> {
  const formData = new FormData();
  formData.append('file', file);
  
  const res = await fetch(`${API_HOST}/analyze`, { method: 'POST', body: formData });
  return await handleResponse<AnalyseAnchorImageResponse>(res);
}

export async function fetchInitial(data: FetchInitialRequest): Promise<FetchInitialResponse> {
  const res = await fetch(`${API_HOST}/fetch_initial`, { 
    method: 'POST', 
    headers: { 'Content-Type': 'application/json' }, 
    body: JSON.stringify(data)
  });
  return await handleResponse<FetchInitialResponse>(res);
}

export async function rerank(data: RerankRequest): Promise<FetchInitialResponse> {
  // Same envelope as `/fetch_initial`, plus `new_items` for the extra page.
  const res = await fetch(`${API_HOST}/rerank`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  return await handleResponse<FetchInitialResponse>(res);
}

export async function rerankBatch(data: BatchRerankRequest): Promise<FetchInitialResponse> {
  // One request for every queued pick: the server fetches one page and reranks once,
  // so the grid updates a single time.
  const res = await fetch(`${API_HOST}/rerank_batch`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  return await handleResponse<FetchInitialResponse>(res);
}

export async function fetchTraitProfile(uploadId: number, itemUrl?: string): Promise<TraitProfileResponse> {
  const params = new URLSearchParams({ upload_id: String(uploadId) });
  if (itemUrl) params.set('item_url', itemUrl);

  const res = await fetch(`${API_HOST}/trait-profile?${params.toString()}`);
  return await handleResponse<TraitProfileResponse>(res);
}

type ItemComparisonRequest = components['schemas']['ItemComparisonRequest'];
type ItemComparisonResponse = components['schemas']['ItemComparisonResponse'];

export async function compare(data: ItemComparisonRequest): Promise<ItemComparisonResponse> {
  const res = await fetch(`/compare`, { 
    method: 'POST', 
    headers: { 'Content-Type': 'application/json' }, 
    body: JSON.stringify(data)
  });
  return await handleResponse<ItemComparisonResponse>(res);
}