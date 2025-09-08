import { useState, useCallback, useEffect, useRef } from 'react';
import { DropArea } from '@/components/DropArea';
import { uploadValueSSE } from '@/lib/api';
import { FileRejection } from 'react-dropzone';
import { AlertTriangle, CheckCircle, Loader2 } from 'lucide-react';

type Status = 'idle' | 'uploading' | 'processing' | 'done' | 'error';

type Message = {
  type: 'status' | 'result' | 'error';
  content: string;
  timestamp: string;
};

const Value2Page = () => {
  const [excelFiles, setExcelFiles] = useState<File[]>([]);
  const [pdfFiles, setPdfFiles] = useState<File[]>([]);
  const [jobId, setJobId] = useState<string | null>(null);
  const [status, setStatus] = useState<Status>('idle');
  const [downloadUrl, setDownloadUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [queryFields, setQueryFields] = useState<string[] | null>(null);
  const [queryTargets, setQueryTargets] = useState<string[] | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);

  const eventSourceRef = useRef<EventSource | null>(null);

  const addMessage = useCallback((type: Message['type'], content: string) => {
    setMessages(prev => [...prev, { type, content, timestamp: new Date().toLocaleTimeString() }]);
  }, []);

  const resetState = useCallback(() => {
    // 送出前不要清空使用者已選檔案；僅清舊訊息與狀態
    setMessages([]);
    setError(null);
    setStatus('idle');
    setDownloadUrl(null);
    setQueryFields(null);
    setQueryTargets(null);
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }
  }, []);

  // 正確：根據 job_id 訂閱 SSE
  function subscribeToJob(jobId: string) {
    const sseUrl = `/api/value/subscribe_sse/${encodeURIComponent(jobId)}`;
    const es = new EventSource(sseUrl);
    eventSourceRef.current = es;

    // 少數後端會用 default message；大多用自定義事件名稱
    es.onmessage = (e) => {
      try {
        const payload = JSON.parse(e.data);
        addMessage('status', payload?.message ?? '收到訊息');
      } catch {
        addMessage('status', e.data || '收到訊息');
      }
    };

    // 建議用自定義事件名稱：status / result / error
    es.addEventListener('status', (e: MessageEvent) => {
      const data = safeParse(e.data);
      addMessage('status', data?.message ?? '處理中…');
      setStatus((data?.status as any) ?? 'processing');
    });

    es.addEventListener('result', (e: MessageEvent) => {
      const data = safeParse(e.data);
      addMessage('status', data?.message ?? '處理完成');
      setStatus('done');
      setDownloadUrl(data?.download_url ?? null);
      setQueryFields(data?.query_fields ?? null);
      setQueryTargets(data?.query_targets ?? null);
      // 任務完成後可以關閉連線
      es.close();
    });

    es.addEventListener('error', (_e: MessageEvent) => {
      addMessage('error', 'SSE 連線錯誤或已中斷');
      setStatus('error');
      es.close();
    });

    // 逾時保護：若 60 秒都沒有任何事件，就提示失敗
    let lastTick = Date.now();
    const tick = setInterval(() => {
      if (Date.now() - lastTick > 60000) {
        addMessage('error', '等候超時：未收到後端進度事件');
        setStatus('error');
        try { es.close(); } catch {}
        clearInterval(tick);
      }
    }, 5000);

    function safeParse(s: string) {
      try { lastTick = Date.now(); return JSON.parse(s); } catch { return null; }
    }
  }

  const onDrop = useCallback((accepted: File[], rejected: FileRejection[]) => {
    const newExcelFiles: File[] = [];
    const newPdfFiles: File[] = [];

    accepted.forEach(file => {
      const ext = file.name.split('.').pop()?.toLowerCase();
      if (ext === 'xlsx' || ext === 'xls') {
        newExcelFiles.push(file);
      } else if (ext === 'pdf') {
        newPdfFiles.push(file);
      }
    });

    setExcelFiles(prev => {
      const updated = [...prev];
      newExcelFiles.forEach(newFile => {
        const existingIndex = updated.findIndex(f => f.name === newFile.name);
        if (existingIndex > -1) { updated[existingIndex] = newFile; } else { updated.push(newFile); }
      });
      return updated;
    });
    setPdfFiles(prev => {
      const updated = [...prev];
      newPdfFiles.forEach(newFile => {
        const existingIndex = updated.findIndex(f => f.name === newFile.name);
        if (existingIndex > -1) { updated[existingIndex] = newFile; } else { updated.push(newFile); }
      });
      return updated;
    });

    if (rejected.length > 0) { setError('部分檔案無效，請檢查類型或大小。'); } else { setError(null); }
  }, []);

  const handleRemoveFile = useCallback((fileName: string) => {
    setExcelFiles(prev => prev.filter(file => file.name !== fileName));
    setPdfFiles(prev => prev.filter(file => file.name !== fileName));
  }, []);

  const handleSubmit = async () => {
    if (excelFiles.length !== 1) { setError('請上傳且僅上傳一個 Excel 檔案。'); return; }
    if (pdfFiles.length === 0) { setError('請至少上傳一個 PDF 檔案。'); return; }
    
    resetState(); // Clear previous state and messages
    setStatus('uploading');
    addMessage('status', '檔案上傳中...');

    try {
      const result = await uploadValueSSE(excelFiles, pdfFiles);
      setJobId(result.job_id);
      setStatus('processing');
      addMessage('status', `任務 ID: ${result.job_id}，等待處理結果...`);

      subscribeToJob(result.job_id);

    } catch (err) {
      setStatus('error');
      const errorMessage = err instanceof Error ? err.message : '上傳失敗，請稍後再試。';
      setError(errorMessage);
      addMessage('error', errorMessage);
    }
  };

  // Cleanup EventSource on component unmount or jobId change
  useEffect(() => {
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
    };
  }, [jobId]); // Add jobId to dependency array

  const allFiles = [...excelFiles, ...pdfFiles];

  return (
    <div className="max-w-5xl mx-auto">
      <h1 className="text-3xl font-bold mb-6">找值 (SSE 測試版)</h1>
      <div className="bg-white dark:bg-gray-800 p-8 rounded-lg shadow-md grid grid-cols-1 md:grid-cols-2 gap-8">
        {/* 左欄：上傳與操作區 */}
        <div className="space-y-6">
          <DropArea
            onDrop={onDrop}
            accept={{
              'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'], 
              'application/vnd.ms-excel': ['.xls'],
              'application/pdf': ['.pdf']
            }}
            maxFiles={0} // 允許無限多個檔案
            title="上傳 Excel 與 PDF 檔案 (1個EXCEL + N個PDF)"
            files={allFiles} // 顯示所有已選檔案
            onRemoveFile={handleRemoveFile}
          />

          {error && (
            <div className="flex items-center gap-2 text-red-700 bg-red-100 dark:bg-red-900/20 p-3 rounded-md">
              <AlertTriangle className="w-5 h-5" />
              <span>{error}</span>
            </div>
          )}

          <button
            onClick={handleSubmit}
            disabled={status === 'uploading' || status === 'processing' || excelFiles.length !== 1 || pdfFiles.length === 0} // Updated disabled condition
            className="w-full bg-blue-600 text-white font-bold py-3 px-4 rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2"
          >
            {(status === 'uploading' || status === 'processing') && <Loader2 className="w-5 h-5 animate-spin" />}
            {status === 'uploading' ? '檔案上傳中...' : 
             status === 'processing' ? '處理中...' : 
             '開始處理'}
          </button>

          {(status === 'done' || status === 'error' || allFiles.length > 0 || messages.length > 0) && (
            <button
              onClick={resetState}
              className="w-full bg-gray-200 text-gray-800 font-bold py-2 px-4 rounded-lg hover:bg-gray-300 dark:bg-gray-700 dark:text-white dark:hover:bg-gray-600 transition-colors"
            >
              清除重傳
            </button>
          )}
        </div>

        {/* 右欄：進度與訊息區 */}
        <div className="space-y-4 pt-4 md:pt-0 md:border-l md:border-gray-200 md:dark:border-gray-700 md:pl-8">
          <h3 className="font-semibold">處理進度與訊息</h3>
          <div className="bg-gray-100 dark:bg-gray-700 p-3 rounded-md h-64 overflow-y-auto text-sm">
            {messages.length === 0 && <p className="text-gray-500">等待上傳檔案...</p>}
            {messages.map((msg, index) => (
              <p key={index} className={msg.type === 'error' ? 'text-red-500' : msg.type === 'result' ? 'text-green-500' : ''}>
                [{msg.timestamp}] {msg.content}
              </p>
            ))}
          </div>

          {queryFields && queryTargets && (
            <div className="bg-blue-50 dark:bg-blue-900/20 p-3 rounded-md text-blue-800 dark:text-blue-200">
              <p className="font-medium">查詢欄位: {queryFields.join(', ')}</p>
              <p className="font-medium">查詢目標: {queryTargets.join(', ')}</p>
            </div>
          )}

          {status === 'done' && downloadUrl && (
            <a
              href={downloadUrl}
              download
              className="flex items-center justify-center gap-2 w-full bg-green-600 text-white font-bold py-3 px-4 rounded-lg hover:bg-green-700 transition-colors mt-4"
            >
              <CheckCircle className="w-5 h-5" />
              下載處理結果 (XLSX)
            </a>
          )}
        </div>
      </div>
    </div>
  );
};

export default Value2Page;
