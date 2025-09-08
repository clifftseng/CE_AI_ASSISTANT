import { useDropzone, FileRejection } from 'react-dropzone';
import { UploadCloud, File as FileIcon, X } from 'lucide-react';
import { useCallback } from 'react';

interface DropAreaProps {
  onDrop: (acceptedFiles: File[], fileRejections: FileRejection[]) => void;
  accept: Record<string, string[]>;
  maxFiles?: number;
  title: string;
  files: File[];
  onRemoveFile?: (fileName: string) => void; 
}

export function DropArea({ onDrop, accept, maxFiles = 0, title, files, onRemoveFile }: DropAreaProps) {
  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop: (acceptedFiles, fileRejections) => {
      console.log('useDropzone onDrop triggered', { acceptedFiles, fileRejections });
      onDrop(acceptedFiles, fileRejections);
    },
    accept,
    maxFiles: maxFiles === 0 ? undefined : maxFiles,
  });

  const handleRemove = useCallback((e: React.MouseEvent, fileName: string) => {
    e.stopPropagation();
    if (onRemoveFile) {
      onRemoveFile(fileName);
    }
  }, [onRemoveFile]);

  return (
    <div className="flex flex-col gap-4">
      <h3 className="font-semibold text-lg">{title}</h3>
      <div
        {...getRootProps()}
        style={{ zIndex: 10 }} // Added z-index for debugging
        className={`p-8 border-2 border-dashed rounded-lg cursor-pointer text-center transition-colors
        ${isDragActive ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20' : 'border-gray-300 dark:border-gray-600 hover:border-gray-400'}`}
      >
        <input {...getInputProps()} />
        <div className="flex flex-col items-center gap-2 text-gray-500 dark:text-gray-400">
          <UploadCloud className="w-10 h-10" />
          {isDragActive ? (
            <p>將檔案拖放到這裡...</p>
          ) : (
            <p>點擊或拖曳檔案至此處上傳</p>
          )}
          <p className="text-xs">
            {maxFiles === 1 ? '僅限單一檔案' : `最多 ${maxFiles === 0 ? '不限' : maxFiles} 個檔案`}
          </p>
          <p className="text-xs text-gray-400">
            支援格式: {Object.values(accept).flat().join(', ')}
          </p>
        </div>
      </div>
      {files.length > 0 && (
        <div className="mt-2 space-y-2">
          <h4 className="text-sm font-medium">已選檔案 ({files.length}):</h4>
          <ul className="space-y-1">
            {files.map((file, i) => (
              <li key={file.name + i} className="flex items-center justify-between text-sm bg-gray-100 dark:bg-gray-700 p-2 rounded">
                <div className="flex items-center gap-2 overflow-hidden">
                  <FileIcon className="w-4 h-4 flex-shrink-0" />
                  <span className="truncate">{file.name}</span>
                  <span className="text-gray-500 flex-shrink-0">({(file.size / 1024).toFixed(1)} KB)</span>
                </div>
                {onRemoveFile && (
                  <button 
                    onClick={(e) => handleRemove(e, file.name)}
                    className="text-gray-500 hover:text-red-500 p-1 rounded-full hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors flex-shrink-0"
                    aria-label={`移除檔案 ${file.name}`}
                  >
                    <X className="w-4 h-4" />
                  </button>
                )}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
