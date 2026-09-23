import React, { useState, useEffect, useRef } from 'react';
import { Search, X, ArrowRight, Tag } from 'lucide-react';
import { searchCorpus, SearchResultItem } from '../services/api';

interface CorpusSearchModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSelectDocument: (id: string) => void;
  isDark: boolean;
}

const FILTER_ARCHETYPES = [
  'Invoice', 'Resume', 'Contract', 'Report', 'Policy Document',
  'Memo', 'Purchase Order', 'Non-Disclosure Agreement', 'Term Sheet',
  'Letter', 'Specification', 'Meeting Minutes', 'Proposal'
];

export const CorpusSearchModal: React.FC<CorpusSearchModalProps> = ({
  isOpen,
  onClose,
  onSelectDocument,
  isDark,
}) => {
  const [query, setQuery] = useState('');
  const [archetypeFilter, setArchetypeFilter] = useState('');
  const [results, setResults] = useState<SearchResultItem[]>([]);
  const [loading, setLoading] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (isOpen) {
      setTimeout(() => inputRef.current?.focus(), 50);
      handleSearch('', '');
    }
  }, [isOpen]);

  const handleSearch = async (q: string, arch: string) => {
    setLoading(true);
    try {
      const res = await searchCorpus(q, arch);
      setResults(res.results);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const onQueryChange = (val: string) => {
    setQuery(val);
    handleSearch(val, archetypeFilter);
  };

  const onArchetypeChange = (arch: string) => {
    const nextArch = archetypeFilter === arch ? '' : arch;
    setArchetypeFilter(nextArch);
    handleSearch(query, nextArch);
  };

  if (!isOpen) return null;

  const modalCls = isDark
    ? 'w-full max-w-3xl bg-[#0f172a] border border-slate-700 rounded-lg shadow-2xl overflow-hidden flex flex-col max-h-[80vh]'
    : 'w-full max-w-3xl bg-white border border-slate-200 rounded-lg shadow-2xl overflow-hidden flex flex-col max-h-[80vh]';

  const searchBarCls = isDark
    ? 'p-3 border-b border-slate-800 flex items-center space-x-3 bg-slate-900/80'
    : 'p-3 border-b border-slate-200 flex items-center space-x-3 bg-slate-50';

  const filterBarCls = isDark
    ? 'px-3 py-2 border-b border-slate-800/80 bg-slate-950/40 flex items-center space-x-1 overflow-x-auto text-[11px] font-mono'
    : 'px-3 py-2 border-b border-slate-200 bg-slate-50/80 flex items-center space-x-1 overflow-x-auto text-[11px] font-mono';

  const inputCls = isDark
    ? 'w-full bg-transparent text-sm text-slate-100 placeholder-slate-500 focus:outline-none font-mono'
    : 'w-full bg-transparent text-sm text-slate-800 placeholder-slate-400 focus:outline-none font-mono';

  const closeBtnCls = isDark
    ? 'p-1 rounded text-slate-400 hover:text-white hover:bg-slate-800 transition'
    : 'p-1 rounded text-slate-500 hover:text-slate-900 hover:bg-slate-100 transition';

  const resultItemCls = isDark
    ? 'p-3 hover:bg-slate-800/50 rounded cursor-pointer transition flex flex-col space-y-1.5'
    : 'p-3 hover:bg-slate-50 rounded cursor-pointer transition flex flex-col space-y-1.5';

  const snippetCls = isDark
    ? 'text-xs text-slate-300 font-mono leading-relaxed bg-slate-950/60 p-2 rounded border border-slate-900'
    : 'text-xs text-slate-600 font-mono leading-relaxed bg-slate-50 p-2 rounded border border-slate-200';

  const footerCls = isDark
    ? 'p-2 border-t border-slate-800 bg-slate-950 flex justify-between items-center text-[10px] font-mono text-slate-500'
    : 'p-2 border-t border-slate-200 bg-slate-50 flex justify-between items-center text-[10px] font-mono text-slate-400';

  return (
    <div className="fixed inset-0 z-50 bg-black/60 flex items-start justify-center pt-16 px-4">
      <div className={modalCls}>
        <div className={searchBarCls}>
          <Search className="w-4 h-4 text-sky-400 shrink-0" />
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={(e) => onQueryChange(e.target.value)}
            placeholder="Search documents, entities, clauses..."
            className={inputCls}
            onKeyDown={(e) => {
              if (e.key === 'Escape') onClose();
            }}
          />
          <button onClick={onClose} className={closeBtnCls}>
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className={filterBarCls}>
          <span className={isDark ? 'text-slate-500 pr-1' : 'text-slate-400 pr-1'}>Filter:</span>
          {FILTER_ARCHETYPES.map((arch) => (
            <button
              key={arch}
              onClick={() => onArchetypeChange(arch)}
              className={`px-2 py-0.5 rounded transition ${
                archetypeFilter === arch
                  ? 'bg-sky-500 text-white font-bold'
                  : isDark
                  ? 'bg-slate-900 text-slate-400 hover:text-slate-200 border border-slate-800'
                  : 'bg-white text-slate-500 hover:text-slate-700 border border-slate-200'
              }`}
            >
              {arch}
            </button>
          ))}
          {loading && <span className="text-sky-400 pl-2 animate-pulse text-[10px]">Searching...</span>}
        </div>

        <div className={`flex-1 overflow-y-auto divide-y p-2 ${isDark ? 'divide-slate-800/60' : 'divide-slate-100'}`}>
          {results.length === 0 ? (
            <div className={`p-8 text-center font-mono text-xs ${isDark ? 'text-slate-500' : 'text-slate-400'}`}>
              No results for "{query}".
            </div>
          ) : (
            results.map((res) => (
              <div
                key={res.id}
                onClick={() => {
                  onSelectDocument(res.id);
                  onClose();
                }}
                className={resultItemCls}
              >
                <div className="flex items-center justify-between text-xs">
                  <div className="flex items-center space-x-2">
                    <span className={`font-semibold ${isDark ? 'text-slate-200' : 'text-slate-800'}`}>{res.filename}</span>
                    <span className={`px-1.5 rounded text-[10px] font-mono border ${isDark ? 'bg-slate-900 border-slate-800 text-sky-400' : 'bg-sky-50 border-sky-200 text-sky-600'}`}>
                      {res.archetype}
                    </span>
                  </div>
                  <div className={`flex items-center space-x-1 text-xs ${isDark ? 'text-slate-400 hover:text-sky-400' : 'text-slate-400 hover:text-sky-500'}`}>
                    <span>Open</span>
                    <ArrowRight className="w-3 h-3" />
                  </div>
                </div>

                <div
                  className={snippetCls}
                  dangerouslySetInnerHTML={{ __html: res.snippet }}
                />

                <div className={`flex items-center space-x-1.5 text-[10px] font-mono ${isDark ? 'text-slate-500' : 'text-slate-400'}`}>
                  <Tag className="w-3 h-3" />
                  <span>{res.critical_keywords.slice(0, 5).join(', ')}</span>
                </div>
              </div>
            ))
          )}
        </div>

        <div className={footerCls}>
          <span>{results.length} results</span>
          <span>ESC to close</span>
        </div>
      </div>
    </div>
  );
};
