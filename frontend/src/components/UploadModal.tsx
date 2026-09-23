import React, { useState, useRef } from 'react';
import { UploadCloud, X, AlertCircle } from 'lucide-react';
import { uploadDocument, DocumentIntelligence } from '../services/api';

interface UploadModalProps {
  isOpen: boolean;
  onClose: () => void;
  onUploaded: (doc: DocumentIntelligence) => void;
  isDark: boolean;
}

export const UploadModal: React.FC<UploadModalProps> = ({
  isOpen,
  onClose,
  onUploaded,
  isDark,
}) => {
  const [dragActive, setDragActive] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  if (!isOpen) return null;

  const handleFile = async (file: File) => {
    setError(null);
    setUploading(true);
    try {
      const doc = await uploadDocument(file);
      onUploaded(doc);
      onClose();
    } catch (err: any) {
      setError(err.message || 'Upload failed');
    } finally {
      setUploading(false);
    }
  };

  const onDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFile(e.dataTransfer.files[0]);
    }
  };

  const modalCls = isDark
    ? 'w-full max-w-lg bg-[#0f172a] border border-slate-700 rounded-lg shadow-2xl overflow-hidden flex flex-col'
    : 'w-full max-w-lg bg-white border border-slate-200 rounded-lg shadow-2xl overflow-hidden flex flex-col';

  const headerCls = isDark
    ? 'p-3 border-b border-slate-800 flex items-center justify-between bg-slate-900/80'
    : 'p-3 border-b border-slate-200 flex items-center justify-between bg-slate-50';

  const dropzoneCls = `border-2 border-dashed rounded-lg p-8 flex flex-col items-center justify-center cursor-pointer transition text-center ${
    dragActive
      ? 'border-sky-400 bg-sky-500/10'
      : isDark
      ? 'border-slate-700 hover:border-slate-500 bg-slate-950/50'
      : 'border-slate-200 hover:border-slate-400 bg-slate-50'
  }`;

  const footerCls = isDark
    ? 'p-3 border-t border-slate-800 bg-slate-950 flex justify-end space-x-2'
    : 'p-3 border-t border-slate-200 bg-slate-50 flex justify-end space-x-2';

  const cancelBtnCls = isDark
    ? 'px-3 py-1.5 rounded bg-slate-900 border border-slate-800 hover:bg-slate-800 text-slate-300 text-xs font-mono transition'
    : 'px-3 py-1.5 rounded bg-white border border-slate-200 hover:bg-slate-100 text-slate-600 text-xs font-mono transition';

  const closeBtnCls = isDark
    ? 'p-1 rounded text-slate-400 hover:text-white hover:bg-slate-800 transition'
    : 'p-1 rounded text-slate-500 hover:text-slate-900 hover:bg-slate-100 transition';

  return (
    <div className="fixed inset-0 z-50 bg-black/60 flex items-center justify-center p-4">
      <div className={modalCls}>
        <div className={headerCls}>
          <div className="flex items-center space-x-2">
            <UploadCloud className="w-4 h-4 text-sky-400" />
            <span className={`font-semibold text-xs uppercase tracking-wider font-mono ${isDark ? 'text-slate-200' : 'text-slate-700'}`}>
              Upload Document
            </span>
          </div>
          <button onClick={onClose} disabled={uploading} className={closeBtnCls}>
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="p-6">
          <div
            onDragOver={(e) => { e.preventDefault(); setDragActive(true); }}
            onDragLeave={() => setDragActive(false)}
            onDrop={onDrop}
            onClick={() => fileInputRef.current?.click()}
            className={dropzoneCls}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf,.docx,.doc,.png,.jpg,.jpeg,.webp"
              className="hidden"
              onChange={(e) => {
                if (e.target.files && e.target.files[0]) {
                  handleFile(e.target.files[0]);
                }
              }}
            />

            <UploadCloud className="w-10 h-10 text-sky-400 mb-3" />
            <p className={`text-sm font-semibold ${isDark ? 'text-slate-200' : 'text-slate-700'}`}>
              Click to select or drag a file here
            </p>
            <p className={`text-xs mt-1 font-mono ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>
              PDF, DOCX, PNG, JPG — Max 25 MB
            </p>
          </div>

          {uploading && (
            <div className={`mt-4 p-3 rounded flex items-center space-x-3 text-xs font-mono text-sky-400 ${isDark ? 'bg-slate-900 border border-slate-800' : 'bg-sky-50 border border-sky-200'}`}>
              <div className="w-4 h-4 border-2 border-sky-400 border-t-transparent rounded-full animate-spin"></div>
              <span>Processing document...</span>
            </div>
          )}

          {error && (
            <div className="mt-4 p-3 bg-rose-950/60 border border-rose-800/80 rounded flex items-center space-x-2 text-xs text-rose-300 font-mono">
              <AlertCircle className="w-4 h-4 text-rose-400 shrink-0" />
              <span>{error}</span>
            </div>
          )}
        </div>

        <div className={footerCls}>
          <button onClick={onClose} disabled={uploading} className={cancelBtnCls}>
            Cancel
          </button>
        </div>
      </div>
    </div>
  );
};
