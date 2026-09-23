import React from 'react';
import { Upload, Database, Search, Cpu, RefreshCw, Sun, Moon } from 'lucide-react';
import { SystemStats } from '../services/api';

interface HeaderProps {
  stats: SystemStats | null;
  onOpenUpload: () => void;
  onOpenSearch: () => void;
  onSeedData: () => void;
  isSeeding: boolean;
  isDark: boolean;
  onToggleTheme: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  stats,
  onOpenUpload,
  onOpenSearch,
  onSeedData,
  isSeeding,
  isDark,
  onToggleTheme,
}) => {
  const formatBytes = (bytes: number) => {
    if (!bytes) return '0 KB';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${(bytes / Math.pow(k, i)).toFixed(1)} ${sizes[i]}`;
  };

  const headerCls = isDark
    ? 'h-14 border-b border-slate-800 bg-[#0f172a] px-4 flex items-center justify-between select-none'
    : 'h-14 border-b border-slate-200 bg-white px-4 flex items-center justify-between select-none shadow-sm';

  const badgeCls = isDark
    ? 'flex items-center space-x-1.5 px-2.5 py-1 rounded-md bg-slate-900 border border-slate-800 text-slate-300'
    : 'flex items-center space-x-1.5 px-2.5 py-1 rounded-md bg-slate-100 border border-slate-200 text-slate-600';

  const labelCls = isDark ? 'text-slate-500 text-xs' : 'text-slate-400 text-xs';
  const valueCls = isDark ? 'font-semibold text-slate-200 text-xs' : 'font-semibold text-slate-800 text-xs';

  const searchBtnCls = isDark
    ? 'h-8 px-3 rounded-md bg-slate-900 border border-slate-700 hover:border-slate-500 text-slate-300 hover:text-white flex items-center space-x-2 text-xs transition'
    : 'h-8 px-3 rounded-md bg-white border border-slate-200 hover:border-slate-400 text-slate-600 hover:text-slate-900 flex items-center space-x-2 text-xs transition';

  const seedBtnCls = isDark
    ? 'h-8 px-3 rounded-md bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-200 flex items-center space-x-1.5 text-xs font-medium transition disabled:opacity-50'
    : 'h-8 px-3 rounded-md bg-slate-100 hover:bg-slate-200 border border-slate-200 text-slate-700 flex items-center space-x-1.5 text-xs font-medium transition disabled:opacity-50';

  const toggleCls = isDark
    ? 'h-8 w-8 flex items-center justify-center rounded-md bg-slate-800 border border-slate-700 text-slate-300 hover:text-white transition'
    : 'h-8 w-8 flex items-center justify-center rounded-md bg-slate-100 border border-slate-200 text-slate-600 hover:text-slate-900 transition';

  const kbdCls = isDark
    ? 'hidden sm:inline-block px-1.5 py-0.5 text-[10px] font-mono bg-slate-800 text-slate-400 border border-slate-700 rounded'
    : 'hidden sm:inline-block px-1.5 py-0.5 text-[10px] font-mono bg-slate-200 text-slate-500 border border-slate-300 rounded';

  return (
    <header className={headerCls}>
      <div className="flex items-center space-x-4">
        <div className="flex items-center space-x-2.5">
          <div className="w-8 h-8 bg-sky-500 rounded-lg flex items-center justify-center shadow-sm">
            <span className="font-bold text-white text-sm font-mono">DS</span>
          </div>
          <span className={`text-base font-bold tracking-tight ${isDark ? 'text-white' : 'text-slate-900'}`}>
            DocSphere
          </span>
        </div>

        <div className={`hidden lg:flex items-center space-x-2 pl-4 border-l text-xs font-mono ${isDark ? 'border-slate-800' : 'border-slate-200'}`}>
          <div className={badgeCls}>
            <Cpu className="w-3.5 h-3.5 text-sky-400" />
            <span className={labelCls}>Engine:</span>
            <span className={valueCls}>{stats?.active_llm_engine || 'Deterministic'}</span>
          </div>
          <div className={badgeCls}>
            <Database className="w-3.5 h-3.5 text-emerald-400" />
            <span className={labelCls}>Docs:</span>
            <span className={valueCls}>{stats?.total_documents ?? 0}</span>
          </div>
          <div className={badgeCls}>
            <span className={labelCls}>Storage:</span>
            <span className={valueCls}>{formatBytes(stats?.storage_size_bytes || 0)}</span>
          </div>
        </div>
      </div>

      <div className="flex items-center space-x-2">
        <button onClick={onOpenSearch} className={searchBtnCls} title="Search (Ctrl+K)">
          <Search className="w-3.5 h-3.5" />
          <span className="hidden sm:inline">Search</span>
          <kbd className={kbdCls}>Ctrl K</kbd>
        </button>

        <button
          onClick={onSeedData}
          disabled={isSeeding}
          className={seedBtnCls}
          title="Load sample documents"
        >
          <RefreshCw className={`w-3.5 h-3.5 text-sky-400 ${isSeeding ? 'animate-spin' : ''}`} />
          <span className="hidden md:inline">{isSeeding ? 'Loading...' : 'Samples'}</span>
        </button>

        <button
          onClick={onOpenUpload}
          className="h-8 px-3 rounded-md bg-sky-500 hover:bg-sky-400 text-white flex items-center space-x-1.5 text-xs font-semibold transition shadow-sm"
        >
          <Upload className="w-3.5 h-3.5" />
          <span>Upload</span>
        </button>

        <button onClick={onToggleTheme} className={toggleCls} title="Toggle theme">
          {isDark ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
        </button>
      </div>
    </header>
  );
};
