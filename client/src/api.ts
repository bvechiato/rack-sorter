import { components } from './types/api'; 

type AnalyseAnchorImageResponse = components['schemas']['AnalyseAnchorImageResponse'];
type FetchInitialRequest = components['schemas']['FetchInitialRequest'];
type FetchInitialResponse = components['schemas']['FetchInitialResponse'];

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

export async function rerank(data: {
  upload_id: number;
  item_url: string;
  feedback_type: string;
  concept?: string;
}) {
  const response = await fetch('/rerank', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    throw new Error('Rerank failed');
  }

  return response.json();
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