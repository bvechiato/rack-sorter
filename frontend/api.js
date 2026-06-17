const API_HOST = window.location.origin;

export async function analyzeFile(file) {
    const formData = new FormData();
    formData.append('file', file);
    const res = await fetch(`${API_HOST}/analyze`, { method: 'POST', body: formData });
    return await res.json();
}

export async function fetchInitial(formData) {
    const res = await fetch(`${API_HOST}/fetch_initial`, { method: 'POST', body: formData });
    return await res.json();
}

export async function rerank(formData) {
    const res = await fetch(`${API_HOST}/rerank`, { method: 'POST', body: formData });
    return await res.json();
}

export default { analyzeFile, fetchInitial, rerank };
