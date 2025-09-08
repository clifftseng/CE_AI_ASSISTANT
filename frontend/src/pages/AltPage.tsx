import { useState, useCallback, useEffect } from 'react';
import { DropArea } from '@/components/DropArea';
import { ProgressBar } from '@/components/ProgressBar';
import { uploadAlt } from '@/lib/api';
import { FileRejection } from 'react-dropzone';
import { AlertTriangle, CheckCircle } from 'lucide-react';

type Status = 'idle' | 'uploading' | 'processing' | 'done' | 'error';

const AltPage = () => {
  const [file, setFile] = useState<File | null>(null);
  const [jobId, setJobId] = useState<string | null>(null);
  const [status, setStatus] = useState<Status>('idle');
  const [progress, setProgress] = useState(0);
  const [progressMessage, setProgressMessage] = useState('');
  const [partialText, setPartialText] = useState('');
  const [downloadUrl, setDownloadUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [metadata, setMetadata] = useState<{ query_fields: string[]; query_targets: string[] } | null>(null);

  const resetState = useCallback(() => {
    setFile(null);
    setJobId(null);
    setStatus('idle');
    setProgress(0);
    setProgressMessage('');
    setPartialText('');
    setDownloadUrl(null);
    setError(null);
    setMetadata(null);
  }, []);

  const onDrop = useCallback((acceptedFiles: File[], fileRejections: FileRejection[]) => {
    console.log('onDrop triggered in AltPage', { acceptedFiles, fileRejections });
    if (fileRejections.length > 0) {
      setError(`檔案無效: ${fileRejections[0].errors[0].message || '請檢查檔案類型或大小'}`);
      setFile(null);
    } else if (acceptedFiles.length > 0) {
      setFile(acceptedFiles[0]);
      console.log('File state after set:', acceptedFiles[0]);
      setError(null);
    }
  }, [resetState]);

  const handleRemoveFile = useCallback(() => {
    resetState();
  }, [resetState]);

  console.log('Button disabled check:', { file: !!file, status });

  const handleSubmit = async () => {
    if (!file) {
      setError('請先選擇一個檔案');
      return;
    }
    
    setStatus('uploading');
    setError(null);
    setProgress(0);
    setProgressMessage('檔案上傳中...');

    try {
      const result = await uploadAlt(file);
      setJobId(result.job_id);
      setStatus('processing');
    } catch (err) {
      setStatus('error');
      setError(err instanceof Error ? err.message : '上傳失敗，請稍後再試。');
    }
  };

  useEffect(() => {
    if (status !== 'processing' || !jobId) return;

    const eventSource = new EventSource(`/api/alt/stream/${jobId}`);
    setProgressMessage('等待後端處理...');

    eventSource.addEventListener('progress', (e) => {
      try {
        const data = JSON.parse(e.data);
        setProgress(data.percent);
        setProgressMessage(data.message);
      } catch (parseError) {
        console.error("Failed to parse progress event data:", parseError);
      }
    });

    eventSource.addEventListener('partial', (e) => {
      try {
        const data = JSON.parse(e.data);
        setPartialText((prev) => prev + data.text);
      } catch (parseError) {
        console.error("Failed to parse partial event data:", parseError);
      }
    });

    eventSource.addEventListener('metadata', (e) => {
      try {
        const data = JSON.parse(e.data);
        setMetadata(data);
        setProgressMessage('已提取查詢欄位與目標。');
      } catch (parseError) {
        console.error("Failed to parse metadata event data:", parseError);
      }
    });

    eventSource.addEventListener('done', (e) => {
      try {
        const data = JSON.parse(e.data);
        setDownloadUrl(data.download_url);
        setStatus('done');
        setProgress(100);
        setProgressMessage('處理完成！');
      } catch (parseError) {
        console.error("處理完成，但解析結果失敗。", parseError);
        setError("處理完成，但解析結果失敗。");
        setStatus('error');
      } finally {
        eventSource.close();
      }
    });

    eventSource.onerror = (err) => {
      console.error("EventSource failed:", err);
      setError('與伺服器連線發生錯誤或處理失敗。');
      setStatus('error');
      eventSource.close();
    };

    return () => {
      eventSource.close();
    };
  }, [status, jobId]);

  return (
    <div className="max-w-5xl mx-auto">
      <h1 className="text-3xl font-bold mb-6">找替代料</h1>
      <div className="bg-white dark:bg-gray-800 p-8 rounded-lg shadow-md grid grid-cols-1 md:grid-cols-2 gap-8">
        {/* 左欄：上傳與操作區 */}
        <div className="space-y-6">
          <DropArea
            onDrop={onDrop}
            accept={{ 
              'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'], 
              'application/vnd.ms-excel': ['.xls'] 
            }}
            maxFiles={1}
            title="上傳 Excel 檔案"
            files={file ? [file] : []}
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
            disabled={!file || status === 'uploading' || status === 'processing'}
            className="w-full bg-blue-600 text-white font-bold py-3 px-4 rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
          >
            {status === 'uploading' ? '檔案上傳中...' : 
             status === 'processing' ? '處理中...' : 
             '送出分析'}
          </button>
          
          {(status === 'done' || status === 'error' || file) && (
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
          {metadata && (
            <div className="bg-blue-50 dark:bg-blue-900/20 p-3 rounded-md text-blue-800 dark:text-blue-200">
              <p className="font-medium">查詢欄位: {metadata.query_fields.join(', ')}</p>
              <p className="font-medium">查詢目標: {metadata.query_targets.join(', ')}</p>
            </div>
          )}
          {(status === 'processing' || status === 'done' || status === 'uploading') ? (
            <>
              <ProgressBar value={progress} />
              <p className="text-sm text-gray-600 dark:text-gray-300">{progressMessage}</p>
              {partialText && (
                <div className="mt-4 p-4 bg-gray-100 dark:bg-gray-900 rounded-md max-h-60 overflow-y-auto border border-gray-200 dark:border-gray-700">
                  <pre className="text-sm whitespace-pre-wrap font-mono text-gray-800 dark:text-gray-200">{partialText}</pre>
                </div>
              )}
            </>
          ) : (
            <p className="text-sm text-gray-500 dark:text-gray-400">等待檔案上傳和分析...</p>
          )}

          {status === 'done' && downloadUrl && (
            <a
              href={downloadUrl}
              download
              className="flex items-center justify-center gap-2 w-full bg-green-600 text-white font-bold py-3 px-4 rounded-lg hover:bg-green-700 transition-colors mt-4"
            >
              <CheckCircle className="w-5 h-5" />
              下載結果
            </a>
          )}
        </div>
      </div>
    </div>
  );
};

export default AltPage;
