const API_BASE = "/api";

export async function uploadAlt(file: File): Promise<{ job_id: string }> {
    const formData = new FormData();
    formData.append("file", file);

    const response = await fetch(`${API_BASE}/alt/upload`, {
        method: 'POST',
        body: formData,
    });

    if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: '未知錯誤' }));
        throw new Error(errorData.detail || '上傳失敗');
    }
    return response.json();
}

export async function uploadValuePolling(
    excelFiles: File[], 
    pdfFiles: File[]
): Promise<{ job_id: string }> {
    const formData = new FormData();
    excelFiles.forEach(file => formData.append('excels', file));
    pdfFiles.forEach(file => formData.append('pdfs', file));

    const response = await fetch(`${API_BASE}/value/upload_polling`, {
        method: 'POST',
        body: formData,
    });

    if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: '未知錯誤' }));
        throw new Error(errorData.detail || '上傳失敗');
    }
    return response.json();
}

export async function pollValuePollingResult(jobId: string): Promise<{ status: string; message?: string; download_url: string | null; query_fields?: string[] | null; query_targets?: string[] | null; }> {
    const response = await fetch(`${API_BASE}/value/result_polling/${jobId}`);
    if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: '未知錯誤' }));
        throw new Error(errorData.detail || '查詢結果失敗');
    }
    return response.json();
}

export async function uploadValueSSE(
    excelFiles: File[], 
    pdfFiles: File[]
): Promise<{ job_id: string }> {
    const formData = new FormData();
    excelFiles.forEach(file => formData.append('excels', file));
    pdfFiles.forEach(file => formData.append('pdfs', file));

    const response = await fetch(`${API_BASE}/value/upload_sse`, {
        method: 'POST',
        body: formData,
    });

    if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: '未知錯誤' }));
        throw new Error(errorData.detail || '上傳失敗');
    }
    return response.json();
}

