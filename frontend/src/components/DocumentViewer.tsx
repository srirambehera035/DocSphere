import React, { useState } from 'react';
import { ExternalLink, FileText, Eye, Download, Code } from 'lucide-react';
import { DocumentIntelligence } from '../services/api';

interface DocumentViewerProps {
  document: DocumentIntelligence | null;
  loading: boolean;
  isDark: boolean;
}

export const DocumentViewer: React.FC<DocumentViewerProps> = ({ document, loading, isDark }) => {
  const [viewMode, setViewMode] = useState<'preview' | 'raw'>('preview');

  const containerCls = isDark
    ? 'h-full flex flex-col bg-[#070a12] border-r border-slate-800'
    : 'h-full flex flex-col bg-slate-50 border-r border-slate-200';

  const toolbarCls = isDark
    ? 'h-10 border-b border-slate-800 bg-slate-900/60 px-3 flex items-center justify-between text-xs font-mono select-none'
    : 'h-10 border-b border-slate-200 bg-white px-3 flex items-center justify-between text-xs font-mono select-none';

  const spinnerColor = isDark ? 'border-sky-500' : 'border-sky-400';

  if (loading) {
    return (
      <div className={`${containerCls} items-center justify-center text-slate-500 font-mono text-xs`}>
        <div className="flex flex-col items-center space-y-2">
          <div className={`w-5 h-5 border-2 border-t-transparent rounded-full animate-spin ${spinnerColor}`}></div>
          <span className={isDark ? 'text-slate-500' : 'text-slate-400'}>Loading...</span>
        </div>
      </div>
    );
  }

  if (!document) {
    return (
      <div className={`${containerCls} items-center justify-center p-8 text-center font-mono text-xs`}>
        <FileText className={`w-10 h-10 mb-3 stroke-[1.5] ${isDark ? 'text-slate-700' : 'text-slate-300'}`} />
        <p className={`font-semibold ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>No document selected</p>
        <p className={`mt-1 max-w-xs text-[11px] ${isDark ? 'text-slate-600' : 'text-slate-400'}`}>
          Upload or select a document to preview it here.
        </p>
      </div>
    );
  }

  const isPdf = document.filename.toLowerCase().endsWith('.pdf');
  const formatBytes = (bytes: number) => {
    if (!bytes) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${(bytes / Math.pow(k, i)).toFixed(1)} ${sizes[i]}`;
  };

  const segBg = isDark ? 'bg-slate-950 border-slate-800' : 'bg-slate-100 border-slate-200';
  const segActive = isDark ? 'bg-slate-800 text-sky-400' : 'bg-white text-sky-600 shadow-sm';
  const segInactive = isDark ? 'text-slate-400 hover:text-slate-200' : 'text-slate-500 hover:text-slate-700';
  const linkCls = isDark
    ? 'p-1 rounded bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-400 hover:text-slate-200 transition'
    : 'p-1 rounded bg-slate-100 hover:bg-slate-200 border border-slate-200 text-slate-500 hover:text-slate-700 transition';

  return (
    <div className={containerCls}>
      <div className={toolbarCls}>
        <div className="flex items-center space-x-2 truncate pr-2">
          <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
          <span className={`font-medium truncate max-w-[200px] ${isDark ? 'text-slate-200' : 'text-slate-700'}`} title={document.filename}>
            {document.filename}
          </span>
          <span className={isDark ? 'text-slate-500' : 'text-slate-400'}>({formatBytes(document.file_size_bytes)})</span>
        </div>

        <div className="flex items-center space-x-1.5 shrink-0">
          <div className={`flex p-0.5 rounded border ${segBg}`}>
            <button
              onClick={() => setViewMode('preview')}
              className={`px-2 py-0.5 rounded text-[11px] font-medium transition ${viewMode === 'preview' ? segActive : segInactive}`}
            >
              <Eye className="w-3 h-3 inline mr-1" />Preview
            </button>
            <button
              onClick={() => setViewMode('raw')}
              className={`px-2 py-0.5 rounded text-[11px] font-medium transition ${viewMode === 'raw' ? segActive : segInactive}`}
            >
              <Code className="w-3 h-3 inline mr-1" />Raw
            </button>
          </div>

          <a href={document.file_url} target="_blank" rel="noreferrer" className={linkCls} title="Open in new tab">
            <ExternalLink className="w-3.5 h-3.5" />
          </a>
          <a href={document.file_url} download={document.filename} className={linkCls} title="Download">
            <Download className="w-3.5 h-3.5" />
          </a>
        </div>
      </div>

      <div className={`flex-1 relative overflow-hidden ${isDark ? 'bg-[#050810]' : 'bg-white'}`}>
        {viewMode === 'preview' ? (
          isPdf ? (
            <iframe
              src={`${document.file_url}#toolbar=1&navpanes=0`}
              className="w-full h-full border-0"
              title={document.filename}
            />
          ) : (
            <div className={`w-full h-full p-6 overflow-auto font-mono text-xs leading-relaxed whitespace-pre-wrap ${isDark ? 'text-slate-300' : 'text-slate-700'}`}>
              {document.extracted_text_full}
            </div>
          )
        ) : (
          <div className={`w-full h-full p-4 overflow-auto font-mono text-xs leading-relaxed whitespace-pre-wrap select-text ${isDark ? 'bg-[#030712] text-slate-300' : 'bg-slate-50 text-slate-700'}`}>
            <div className={`pb-2 mb-3 border-b text-[11px] uppercase tracking-wider flex justify-between ${isDark ? 'border-slate-800 text-slate-500' : 'border-slate-200 text-slate-400'}`}>
              <span>Raw text ({document.extracted_text_full.length} chars)</span>
              <span>{document.processing_time_ms} ms</span>
            </div>
            {document.extracted_text_full}
          </div>
        )}
      </div>
    </div>
  );
};
