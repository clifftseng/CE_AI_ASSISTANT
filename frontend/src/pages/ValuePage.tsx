import { useState, useCallback, useEffect } from 'react';
import { DropArea } from '@/components/DropArea';
import { uploadValuePolling, pollValuePollingResult } from '@/lib/api';
import { FileRejection } from 'react-dropzone';
import { AlertTriangle, CheckCircle, Loader2 } from 'lucide-react';

type Status = 'idle' | 'uploading' | 'polling' | 'done' | 'error';

const ValuePage = () => {
  const [excelFiles, setExcelFiles] = useState<File[]>([]);
  const [pdfFiles, setPdfFiles] = useState<File[]>([]);
  const [jobId, setJobId] = useState<string | null>(null);
  const [status, setStatus] = useState<Status>('idle');
  const [downloadUrl, setDownloadUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [queryFields, setQueryFields] = useState<string[] | null>(null);
  const [queryTargets, setQueryTargets] = useState<string[] | null>(null);
  const [processingMessages, setProcessingMessages] = useState<string[]>([]);
  const [excelPreviewContent, setExcelPreviewContent] = useState<string | null>(null); // New state for Excel preview HTML

  const resetState = useCallback(() => {
    setExcelFiles([]);
    setPdfFiles([]);
    setJobId(null);
    setStatus('idle');
    setDownloadUrl(null);
    setError(null);
    setQueryFields(null);
    setQueryTargets(null);
    setProcessingMessages([]);
    setExcelPreviewContent(null); // Reset Excel preview content
  }, []);

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

    // 處理重複檔案：如果已存在同名檔案，則替換
    setExcelFiles(prev => {
      const updated = [...prev];
      newExcelFiles.forEach(newFile => {
        const existingIndex = updated.findIndex(f => f.name === newFile.name);
        if (existingIndex > -1) {
          updated[existingIndex] = newFile;
        } else {
          updated.push(newFile);
        }
      });
      return updated;
    });
    setPdfFiles(prev => {
      const updated = [...prev];
      newPdfFiles.forEach(newFile => {
        const existingIndex = updated.findIndex(f => f.name === newFile.name);
        if (existingIndex > -1) {
          updated[existingIndex] = newFile;
        } else {
          updated.push(newFile);
        }
      });
      return updated;
    });

    if (rejected.length > 0) {
      setError('部分檔案無效，請檢查類型或大小。');
    } else {
      setError(null);
    }
  }, []);

  const handleRemoveFile = useCallback((fileName: string) => {
    setExcelFiles(prev => prev.filter(file => file.name !== fileName));
    setPdfFiles(prev => prev.filter(file => file.name !== fileName));
  }, []);

  const handleSubmit = async () => {
    // 檢查 Excel 檔案數量
    if (excelFiles.length !== 1) {
      setError('請上傳且僅上傳一個 Excel 檔案。');
      return;
    }
    // 檢查 PDF 檔案數量
    if (pdfFiles.length === 0) {
      setError('請至少上傳一個 PDF 檔案。');
      return;
    }
    
    setStatus('uploading');
    setError(null);
    setProcessingMessages([]); // Clear messages on new submission

    try {
      const result = await uploadValuePolling(excelFiles, pdfFiles);
      setJobId(result.job_id);
      setStatus('polling');
    } catch (err) {
      setStatus('error');
      setError(err instanceof Error ? err.message : '上傳失敗，請稍後再試。');
    }
  };

  useEffect(() => {
    if (status !== 'polling' || !jobId) return;

    const interval = setInterval(async () => {
      try {
        const result = await pollValuePollingResult(jobId);
        const timestamp = new Date().toLocaleTimeString();
        if (result.status === 'done') {
          setDownloadUrl(result.download_url);
          setQueryFields(result.query_fields || null);
          setQueryTargets(result.query_targets || null);
          setProcessingMessages(prev => [...prev, `${timestamp}: 處理完成！`]);
          setStatus('done');
          clearInterval(interval);

          // Fetch Excel preview content
          if (result.download_url) {
            const fileId = result.download_url.split('/').pop(); // Extract file_id from download_url
            if (fileId) {
              try {
                const previewResponse = await fetch(`/api/download/preview/${fileId}`);
                if (previewResponse.ok) {
                  const htmlContent = await previewResponse.text();
                  setExcelPreviewContent(htmlContent);
                } else {
                  console.error('Failed to fetch Excel preview:', previewResponse.statusText);
                  setProcessingMessages(prev => [...prev, `${timestamp}: 警告 - 無法載入 Excel 預覽。`]);
                }
              } catch (previewError) {
                console.error('Error fetching Excel preview:', previewError);
                setProcessingMessages(prev => [...prev, `${timestamp}: 錯誤 - 載入 Excel 預覽失敗。`]);
              }
            }
          }
        } else if (result.status === 'error') {
          const errorMessage = result.message || '後端處理失敗，請檢查日誌。';
          setError(errorMessage);
          setProcessingMessages(prev => [...prev, `${timestamp}: 錯誤 - ${errorMessage}`]);
          setStatus('error');
          clearInterval(interval);
        } else {
          // Update message for processing status
          const message = result.message || '後端處理中，請稍候...';
          setProcessingMessages(prev => {
            // Only add if the message is new or significantly different from the last one
            if (prev.length === 0 || prev[prev.length - 1] !== `${timestamp}: ${message}`) {
              return [...prev, `${timestamp}: ${message}`];
            }
            return prev;
          });
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : '輪詢結果失敗，請檢查網路。');
        setStatus('error');
        clearInterval(interval);
      }
    }, 2000);

    return () => clearInterval(interval);
  }, [status, jobId]);

  const allFiles = [...excelFiles, ...pdfFiles];

  return (
    <div className="max-w-5xl mx-auto">
      <h1 className="text-3xl font-bold mb-6">找值</h1>
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

{/*          {allFiles.length > 0 && (
            <div className="mt-2 space-y-2">
              <h4 className="text-sm font-medium">已選檔案 ({allFiles.length}):</h4>
              <ul className="space-y-1">
                {allFiles.map((file, i) => (
                  <li key={file.name + i} className="flex items-center justify-between text-sm bg-gray-100 dark:bg-gray-700 p-2 rounded">
                    <div className="flex items-center gap-2 overflow-hidden">
                      <FileIcon className="w-4 h-4 flex-shrink-0" />
                      <span className="truncate">{file.name}</span>
                      <span className="text-gray-500 flex-shrink-0">({(file.size / 1024).toFixed(1)} KB)</span>
                    </div>
                    <button 
                      onClick={() => handleRemoveFile(file.name)}
                      className="text-gray-500 hover:text-red-500 p-1 rounded-full hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors flex-shrink-0"
                      aria-label={`移除檔案 ${file.name}`}
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </li>
                ))}
              </ul>
            </div>
          )}*/}

          {error && (
            <div className="flex items-center gap-2 text-red-700 bg-red-100 dark:bg-red-900/20 p-3 rounded-md">
              <AlertTriangle className="w-5 h-5" />
              <span>{error}</span>
            </div>
          )}

          <button
            onClick={handleSubmit}
            disabled={status === 'uploading' || status === 'polling' || excelFiles.length !== 1 || pdfFiles.length === 0} // Updated disabled condition
            className="w-full bg-blue-600 text-white font-bold py-3 px-4 rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2"
          >
            {status === 'polling' && <Loader2 className="w-5 h-5 animate-spin" />}
            {status === 'uploading' ? '檔案上傳中...' : 
             status === 'polling' ? '處理中...' : 
             '開始處理'}
          </button>

          {(status === 'done' || status === 'error' || allFiles.length > 0) && (
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
          {queryFields && queryTargets && (
            <div className="bg-blue-50 dark:bg-blue-900/20 p-3 rounded-md text-blue-800 dark:text-blue-200">
              <p className="font-medium">查詢欄位: {queryFields.join(', ')}</p>
              <p className="font-medium">查詢目標: {queryTargets.join(', ')}</p>
            </div>
          )}
          <div className="space-y-2 p-4 bg-gray-100 dark:bg-gray-700 rounded-md h-48 overflow-y-auto">
            {processingMessages.length === 0 && status === 'idle' && (
              <p className="text-gray-500 dark:text-gray-400">等待檔案上傳...</p>
            )}
            {processingMessages.map((msg, index) => (
              <p key={index} className="text-sm text-gray-800 dark:text-gray-200">{msg}</p>
            ))}
            {status === 'uploading' && <p className="text-sm text-gray-800 dark:text-gray-200">檔案上傳中...</p>}
            {status === 'polling' && processingMessages.length === 0 && <p className="text-sm text-gray-800 dark:text-gray-200">後端處理中，請稍候...</p>}
          </div>

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

      {/* Excel Preview Section */}
      {status === 'done' && excelPreviewContent && (
        <div className="mt-8 bg-white dark:bg-gray-800 p-8 rounded-lg shadow-md">
          <h3 className="text-2xl font-bold mb-4">Excel 預覽</h3>
          <div className="overflow-x-auto" dangerouslySetInnerHTML={{ __html: excelPreviewContent }} />
        </div>
      )}
    </div>
  );
};

export default ValuePage;