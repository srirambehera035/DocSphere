import React, { useState } from 'react';
import { Trash2, Search } from 'lucide-react';
import { DocumentSummaryItem, DocumentArchetype } from '../services/api';

interface DocumentListProps {
  documents: DocumentSummaryItem[];
  selectedId: string | null;
  onSelect: (id: string) => void;
  onDelete: (id: string) => void;
  selectedArchetype: string;
  onSelectArchetype: (arch: string) => void;
  loading: boolean;
  isDark: boolean;
}

const ARCHETYPES = [
  'All', 'Invoice', 'Resume', 'Contract', 'Report', 'Policy Document',
  'Memo', 'Purchase Order', 'Non-Disclosure Agreement', 'Term Sheet',
  'Letter', 'Specification', 'Meeting Minutes', 'Proposal'
];

const getArchetypeDot = (arch: DocumentArchetype): string => {
  const map: Record<string, string> = {
    'Invoice': 'bg-amber-400',
    'Resume': 'bg-purple-400',
    'Contract': 'bg-blue-400',
    'Report': 'bg-emerald-400',
    'Policy Document': 'bg-rose-400',
    'Memo': 'bg-orange-400',
    'Purchase Order': 'bg-yellow-400',
    'Non-Disclosure Agreement': 'bg-indigo-400',
    'Term Sheet': 'bg-cyan-400',
    'Letter': 'bg-teal-400',
    'Specification': 'bg-violet-400',
    'Meeting Minutes': 'bg-lime-400',
    'Proposal': 'bg-pink-400',
  };
  return map[arch] || 'bg-slate-400';
};

export const DocumentList: React.FC<DocumentListProps> = ({
  documents,
  selectedId,
  onSelect,
  onDelete,
  selectedArchetype,
  onSelectArchetype,
  loading,
  isDark,
}) => {
  const [filterQuery, setFilterQuery] = useState('');

  const filtered = documents.filter((doc) => {
    const q = filterQuery.trim().toLowerCase();
    if (!q) return true;
    return (
      doc.filename.toLowerCase().includes(q) ||
      doc.archetype.toLowerCase().includes(q) ||
      doc.executive_summary.toLowerCase().includes(q)
    );
  });

  const sidebarCls = isDark
    ? 'w-72 h-full flex flex-col bg-[#0f172a] border-r border-slate-800 shrink-0 select-none'
    : 'w-72 h-full flex flex-col bg-white border-r border-slate-200 shrink-0 select-none';

  const headerAreaCls = isDark
    ? 'p-3 border-b border-slate-800 space-y-2'
    : 'p-3 border-b border-slate-200 space-y-2';

  const labelCls = isDark ? 'text-slate-400 font-bold uppercase tracking-wider' : 'text-slate-500 font-bold uppercase tracking-wider';
  const countCls = isDark
    ? 'px-1.5 rounded bg-slate-900 border border-slate-800 text-slate-300 text-[10px]'
    : 'px-1.5 rounded bg-slate-100 border border-slate-200 text-slate-600 text-[10px]';

  const inputCls = isDark
    ? 'w-full bg-slate-950 border border-slate-800 rounded pl-8 pr-3 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-sky-500'
    : 'w-full bg-slate-50 border border-slate-200 rounded pl-8 pr-3 py-1.5 text-xs text-slate-800 placeholder-slate-400 focus:outline-none focus:border-sky-400';

  const dividerCls = isDark ? 'divide-slate-800/60' : 'divide-slate-100';

  return (
    <div className={sidebarCls}>
      <div className={headerAreaCls}>
        <div className="flex items-center justify-between text-xs font-mono">
          <span className={labelCls}>Documents</span>
          <span className={countCls}>{filtered.length} / {documents.length}</span>
        </div>

        <div className="relative">
          <Search className={`w-3.5 h-3.5 absolute left-2.5 top-2.5 ${isDark ? 'text-slate-500' : 'text-slate-400'}`} />
          <input
            type="text"
            placeholder="Filter..."
            value={filterQuery}
            onChange={(e) => setFilterQuery(e.target.value)}
            className={inputCls}
          />
        </div>

        <div className="flex flex-wrap gap-1">
          {ARCHETYPES.map((arch) => (
            <button
              key={arch}
              onClick={() => onSelectArchetype(arch)}
              className={`px-2 py-0.5 rounded text-[10px] font-mono transition ${
                selectedArchetype === arch
                  ? 'bg-sky-500 text-white font-bold'
                  : isDark
                  ? 'bg-slate-900 text-slate-400 hover:text-slate-200 hover:bg-slate-800'
                  : 'bg-slate-100 text-slate-500 hover:text-slate-700 hover:bg-slate-200'
              }`}
            >
              {arch}
            </button>
          ))}
        </div>
      </div>

      <div className={`flex-1 overflow-y-auto divide-y ${dividerCls}`}>
        {loading && documents.length === 0 ? (
          <div className={`p-6 text-center font-mono text-xs ${isDark ? 'text-slate-500' : 'text-slate-400'}`}>Scanning...</div>
        ) : filtered.length === 0 ? (
          <div className={`p-6 text-center font-mono text-xs ${isDark ? 'text-slate-500' : 'text-slate-400'}`}>No documents found.</div>
        ) : (
          filtered.map((doc) => {
            const isSelected = doc.id === selectedId;
            return (
              <div
                key={doc.id}
                onClick={() => onSelect(doc.id)}
                className={`p-3 cursor-pointer transition flex flex-col space-y-1 ${
                  isSelected
                    ? isDark
                      ? 'bg-slate-800/80 border-l-2 border-sky-400'
                      : 'bg-sky-50 border-l-2 border-sky-400'
                    : isDark
                    ? 'hover:bg-slate-800/40'
                    : 'hover:bg-slate-50'
                }`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-center space-x-2 truncate">
                    <span className={`w-2 h-2 rounded-full shrink-0 ${getArchetypeDot(doc.archetype)}`} />
                    <span
                      className={`text-xs font-medium truncate ${isDark ? 'text-slate-200' : 'text-slate-800'}`}
                      title={doc.filename}
                    >
                      {doc.filename}
                    </span>
                  </div>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      if (confirm(`Delete ${doc.filename}?`)) {
                        onDelete(doc.id);
                      }
                    }}
                    className={`p-1 rounded transition ml-1 ${
                      isDark
                        ? 'text-slate-600 hover:text-rose-400 hover:bg-slate-900'
                        : 'text-slate-400 hover:text-rose-500 hover:bg-slate-100'
                    }`}
                    title="Delete"
                  >
                    <Trash2 className="w-3 h-3" />
                  </button>
                </div>

                <div className={`flex items-center justify-between font-mono text-[10px] ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>
                  <span className={`font-semibold ${isDark ? 'text-slate-300' : 'text-slate-600'}`}>{doc.archetype}</span>
                  <span>{Math.round(doc.archetype_confidence * 100)}%</span>
                </div>

                <p className={`text-[11px] line-clamp-2 leading-relaxed ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>
                  {doc.executive_summary}
                </p>

                <div className={`flex items-center justify-between font-mono text-[9px] pt-0.5 ${isDark ? 'text-slate-600' : 'text-slate-400'}`}>
                  <span>{doc.processing_time_ms}ms</span>
                  <span>{doc.upload_timestamp.slice(0, 10)}</span>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};
