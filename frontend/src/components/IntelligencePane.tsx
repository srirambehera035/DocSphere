import React, { useState } from 'react';
import {
  CheckCircle2, Copy, Download, Check, Sparkles, Calendar, DollarSign,
  Users, AlertCircle, FileSpreadsheet, ShieldAlert, Cpu, BookOpen
} from 'lucide-react';
import { DocumentIntelligence, DocumentArchetype } from '../services/api';

interface IntelligencePaneProps {
  document: DocumentIntelligence | null;
  loading: boolean;
  isDark: boolean;
}

type TabType = 'overview' | 'entities' | 'domain_data' | 'json';

const getArchetypeBadgeClass = (arch: DocumentArchetype, isDark: boolean): string => {
  const darkMap: Record<string, string> = {
    'Invoice': 'bg-amber-950/70 text-amber-300 border-amber-800/80',
    'Resume': 'bg-purple-950/70 text-purple-300 border-purple-800/80',
    'Contract': 'bg-blue-950/70 text-blue-300 border-blue-800/80',
    'Report': 'bg-emerald-950/70 text-emerald-300 border-emerald-800/80',
    'Policy Document': 'bg-rose-950/70 text-rose-300 border-rose-800/80',
    'Memo': 'bg-orange-950/70 text-orange-300 border-orange-800/80',
    'Purchase Order': 'bg-yellow-950/70 text-yellow-300 border-yellow-800/80',
    'Non-Disclosure Agreement': 'bg-indigo-950/70 text-indigo-300 border-indigo-800/80',
    'Term Sheet': 'bg-cyan-950/70 text-cyan-300 border-cyan-800/80',
    'Letter': 'bg-teal-950/70 text-teal-300 border-teal-800/80',
    'Specification': 'bg-violet-950/70 text-violet-300 border-violet-800/80',
    'Meeting Minutes': 'bg-lime-950/70 text-lime-300 border-lime-800/80',
    'Proposal': 'bg-pink-950/70 text-pink-300 border-pink-800/80',
  };
  const lightMap: Record<string, string> = {
    'Invoice': 'bg-amber-50 text-amber-700 border-amber-200',
    'Resume': 'bg-purple-50 text-purple-700 border-purple-200',
    'Contract': 'bg-blue-50 text-blue-700 border-blue-200',
    'Report': 'bg-emerald-50 text-emerald-700 border-emerald-200',
    'Policy Document': 'bg-rose-50 text-rose-700 border-rose-200',
    'Memo': 'bg-orange-50 text-orange-700 border-orange-200',
    'Purchase Order': 'bg-yellow-50 text-yellow-700 border-yellow-200',
    'Non-Disclosure Agreement': 'bg-indigo-50 text-indigo-700 border-indigo-200',
    'Term Sheet': 'bg-cyan-50 text-cyan-700 border-cyan-200',
    'Letter': 'bg-teal-50 text-teal-700 border-teal-200',
    'Specification': 'bg-violet-50 text-violet-700 border-violet-200',
    'Meeting Minutes': 'bg-lime-50 text-lime-700 border-lime-200',
    'Proposal': 'bg-pink-50 text-pink-700 border-pink-200',
  };
  return (isDark ? darkMap[arch] : lightMap[arch]) || (isDark ? 'bg-slate-900 text-slate-300 border-slate-700' : 'bg-slate-100 text-slate-600 border-slate-200');
};

export const IntelligencePane: React.FC<IntelligencePaneProps> = ({ document, loading, isDark }) => {
  const [activeTab, setActiveTab] = useState<TabType>('overview');
  const [copied, setCopied] = useState(false);

  const paneCls = isDark
    ? 'h-full flex flex-col bg-[#0b0f19] text-slate-200'
    : 'h-full flex flex-col bg-white text-slate-800';

  const headerCls = isDark
    ? 'p-3 bg-slate-900/90 border-b border-slate-800 flex flex-col space-y-2'
    : 'p-3 bg-slate-50 border-b border-slate-200 flex flex-col space-y-2';

  const tabActive = isDark
    ? 'bg-sky-500/10 text-sky-400 border border-sky-500/30 font-semibold'
    : 'bg-sky-50 text-sky-600 border border-sky-200 font-semibold';

  const tabInactive = isDark
    ? 'text-slate-400 hover:text-slate-200'
    : 'text-slate-500 hover:text-slate-700';

  const sectionCls = isDark
    ? 'bg-slate-900/50 border border-slate-800 rounded p-3.5'
    : 'bg-slate-50 border border-slate-200 rounded p-3.5';

  const labelCls = isDark ? 'text-slate-400' : 'text-slate-500';
  const textCls = isDark ? 'text-slate-200' : 'text-slate-800';
  const subTextCls = isDark ? 'text-slate-300' : 'text-slate-600';
  const iconBtnCls = isDark
    ? 'p-1 rounded bg-slate-950 border border-slate-800 text-slate-400 hover:text-white transition'
    : 'p-1 rounded bg-slate-100 border border-slate-200 text-slate-500 hover:text-slate-800 transition';
  const rowCls = isDark
    ? 'bg-slate-950 border-slate-800'
    : 'bg-white border-slate-200';
  const rowHover = isDark ? 'border-slate-900 hover:bg-slate-900/50' : 'border-slate-100 hover:bg-slate-100';

  if (loading) {
    return (
      <div className={`${paneCls} items-center justify-center font-mono text-xs`}>
        <div className="flex flex-col items-center space-y-2">
          <div className={`w-5 h-5 border-2 border-t-transparent rounded-full animate-spin ${isDark ? 'border-sky-500' : 'border-sky-400'}`}></div>
          <span className={isDark ? 'text-slate-500' : 'text-slate-400'}>Analyzing...</span>
        </div>
      </div>
    );
  }

  if (!document) {
    return (
      <div className={`${paneCls} items-center justify-center p-8 text-center font-mono text-xs`}>
        <Cpu className={`w-10 h-10 mb-3 stroke-[1.5] ${isDark ? 'text-slate-800' : 'text-slate-300'}`} />
        <p className={`font-semibold ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>AI Intelligence</p>
        <p className={`mt-1 max-w-xs text-[11px] ${isDark ? 'text-slate-600' : 'text-slate-400'}`}>
          Select a document to view structured AI extraction.
        </p>
      </div>
    );
  }

  const handleCopyJson = () => {
    navigator.clipboard.writeText(JSON.stringify(document, null, 2));
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownloadJson = () => {
    const blob = new Blob([JSON.stringify(document, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = window.document.createElement('a');
    a.href = url;
    a.download = `${document.filename}.intelligence.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const totalEntities = document.extracted_entities.dates.length +
    document.extracted_entities.monetary_amounts.length +
    document.extracted_entities.parties.length;

  return (
    <div className={paneCls}>
      <div className={headerCls}>
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <span className={`px-2.5 py-0.5 rounded text-xs font-mono font-bold border ${getArchetypeBadgeClass(document.archetype, isDark)}`}>
              {document.archetype}
            </span>
            <div className="flex items-center space-x-1 text-xs font-mono">
              <span className={labelCls}>Conf:</span>
              <span className="text-emerald-400 font-bold">{Math.round(document.archetype_confidence * 100)}%</span>
            </div>
            <span className={`px-1.5 rounded text-[10px] font-mono border ${isDark ? 'bg-slate-950 border-slate-800 text-slate-400' : 'bg-slate-100 border-slate-200 text-slate-500'}`}>
              {document.page_count}p
            </span>
          </div>

          <div className={`flex items-center space-x-1.5 font-mono text-[11px] ${labelCls}`}>
            <span className={`px-1.5 py-0.5 rounded border ${isDark ? 'bg-slate-950 border-slate-800 text-slate-300' : 'bg-slate-100 border-slate-200 text-slate-600'}`}>
              {document.llm_provider_used}
            </span>
            <span className={isDark ? 'text-slate-500' : 'text-slate-400'}>{document.processing_time_ms}ms</span>
          </div>
        </div>

        <p className={`text-[11px] font-mono leading-tight ${labelCls}`}>
          {document.archetype_rationale}
        </p>

        <div className={`flex items-center space-x-1 pt-1 border-t overflow-x-auto text-xs font-mono ${isDark ? 'border-slate-800/60' : 'border-slate-200'}`}>
          {(['overview', 'entities', 'domain_data', 'json'] as TabType[]).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-3 py-1 rounded transition whitespace-nowrap ${activeTab === tab ? tabActive : tabInactive}`}
            >
              {tab === 'overview' && 'Summary'}
              {tab === 'entities' && `Entities (${totalEntities})`}
              {tab === 'domain_data' && 'Schema'}
              {tab === 'json' && 'JSON'}
            </button>
          ))}

          <div className="ml-auto flex items-center space-x-1 pl-2">
            <button onClick={handleCopyJson} className={iconBtnCls} title="Copy JSON">
              {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
            </button>
            <button onClick={handleDownloadJson} className={iconBtnCls} title="Download JSON">
              <Download className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-4 font-sans text-xs">
        {activeTab === 'overview' && (
          <div className="space-y-4">
            <section className={sectionCls}>
              <div className="flex items-center space-x-1.5 mb-2 text-sky-400 font-mono text-[11px] font-bold uppercase tracking-wider">
                <Sparkles className="w-3.5 h-3.5" />
                <span>Summary</span>
              </div>
              <p className={`leading-relaxed text-xs ${textCls}`}>{document.executive_summary}</p>
            </section>

            {document.operational_summary_points.length > 0 && (
              <section className={sectionCls}>
                <div className={`font-mono text-[11px] font-bold uppercase tracking-wider mb-2 flex items-center space-x-1.5 ${labelCls}`}>
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                  <span>Key Points</span>
                </div>
                <ul className="space-y-2 font-mono text-[11px]">
                  {document.operational_summary_points.map((pt, idx) => (
                    <li key={idx} className={`flex items-start space-x-2 ${subTextCls}`}>
                      <span className={`px-1.5 rounded text-[10px] text-sky-400 shrink-0 ${isDark ? 'bg-slate-800 border border-slate-700' : 'bg-sky-50 border border-sky-200'}`}>
                        p.{pt.page || 1}
                      </span>
                      <span className="leading-snug">{pt.text}</span>
                    </li>
                  ))}
                </ul>
              </section>
            )}

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {document.core_obligations.length > 0 && (
                <section className={sectionCls}>
                  <div className="text-blue-400 font-mono text-[11px] font-bold uppercase tracking-wider mb-2 flex items-center space-x-1">
                    <AlertCircle className="w-3.5 h-3.5" />
                    <span>Obligations</span>
                  </div>
                  <ul className={`space-y-2 text-[11px] ${subTextCls}`}>
                    {document.core_obligations.map((item, idx) => (
                      <li key={idx} className="border-l-2 border-blue-500/60 pl-2 space-y-0.5">
                        <div className="flex items-center space-x-1 font-mono text-[10px] text-blue-400">
                          <BookOpen className="w-3 h-3" />
                          <span>p.{item.page || 1}</span>
                        </div>
                        <p className={`leading-snug ${textCls}`}>{item.text}</p>
                      </li>
                    ))}
                  </ul>
                </section>
              )}

              {document.key_deliverables.length > 0 && (
                <section className={sectionCls}>
                  <div className="text-emerald-400 font-mono text-[11px] font-bold uppercase tracking-wider mb-2 flex items-center space-x-1">
                    <FileSpreadsheet className="w-3.5 h-3.5" />
                    <span>Deliverables</span>
                  </div>
                  <ul className={`space-y-2 text-[11px] ${subTextCls}`}>
                    {document.key_deliverables.map((item, idx) => (
                      <li key={idx} className="border-l-2 border-emerald-500/60 pl-2 space-y-0.5">
                        <div className="font-mono text-[10px] text-emerald-400">p.{item.page || 1}</div>
                        <p className={`leading-snug ${textCls}`}>{item.text}</p>
                      </li>
                    ))}
                  </ul>
                </section>
              )}
            </div>

            {document.liability_clauses.length > 0 && (
              <section className={isDark ? 'bg-rose-950/20 border border-rose-900/40 rounded p-3' : 'bg-rose-50 border border-rose-200 rounded p-3'}>
                <div className="text-rose-400 font-mono text-[11px] font-bold uppercase tracking-wider mb-2 flex items-center space-x-1">
                  <ShieldAlert className="w-3.5 h-3.5" />
                  <span>Liability & Risk</span>
                </div>
                <ul className={`space-y-2 text-[11px] ${subTextCls}`}>
                  {document.liability_clauses.map((clause, idx) => (
                    <li key={idx} className="flex items-start space-x-2">
                      <span className={`px-1.5 rounded text-[10px] text-rose-300 font-mono shrink-0 ${isDark ? 'bg-rose-900/60 border border-rose-800' : 'bg-rose-100 border border-rose-200'}`}>
                        p.{clause.page || 1}
                      </span>
                      <span className="leading-snug">{clause.text}</span>
                    </li>
                  ))}
                </ul>
              </section>
            )}

            {(document.technical_tags.length > 0 || document.critical_keywords.length > 0) && (
              <section className={sectionCls}>
                <div className={`font-mono text-[11px] font-bold uppercase tracking-wider mb-2 ${labelCls}`}>Tags & Keywords</div>
                <div className="flex flex-wrap gap-1.5">
                  {document.technical_tags.map((tag, idx) => (
                    <span key={idx} className={`px-2 py-0.5 rounded font-mono text-[10px] ${isDark ? 'bg-sky-950 text-sky-300 border border-sky-800/80' : 'bg-sky-50 text-sky-600 border border-sky-200'}`}>
                      {tag}
                    </span>
                  ))}
                  {document.critical_keywords.map((kw, idx) => (
                    <span key={idx} className={`px-2 py-0.5 rounded font-mono text-[10px] ${isDark ? 'bg-slate-950 text-slate-300 border border-slate-800' : 'bg-slate-100 text-slate-600 border border-slate-200'}`}>
                      {kw}
                    </span>
                  ))}
                </div>
              </section>
            )}
          </div>
        )}

        {activeTab === 'entities' && (
          <div className="space-y-4 font-mono text-xs">
            <section className={sectionCls}>
              <div className="flex items-center space-x-1.5 text-amber-400 text-[11px] font-bold uppercase mb-2">
                <DollarSign className="w-3.5 h-3.5" />
                <span>Monetary ({document.extracted_entities.monetary_amounts.length})</span>
              </div>
              {document.extracted_entities.monetary_amounts.length === 0 ? (
                <p className={`text-[11px] ${labelCls}`}>No monetary amounts found.</p>
              ) : (
                <div className="space-y-1.5">
                  {document.extracted_entities.monetary_amounts.map((m, idx) => (
                    <div key={idx} className={`p-2 rounded border flex justify-between items-center text-[11px] ${rowCls}`}>
                      <div className="truncate pr-2">
                        <span className="text-emerald-400 font-bold mr-2">
                          {m.currency} {m.amount.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                        </span>
                        <span className={`text-[10px] truncate max-w-sm inline-block ${labelCls}`}>{m.context}</span>
                      </div>
                      <span className={`px-1.5 rounded border text-[10px] text-amber-400 shrink-0 ${isDark ? 'bg-slate-900 border-slate-800' : 'bg-amber-50 border-amber-200'}`}>
                        p.{m.page || 1}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </section>

            <section className={sectionCls}>
              <div className="flex items-center space-x-1.5 text-blue-400 text-[11px] font-bold uppercase mb-2">
                <Calendar className="w-3.5 h-3.5" />
                <span>Dates ({document.extracted_entities.dates.length})</span>
              </div>
              {document.extracted_entities.dates.length === 0 ? (
                <p className={`text-[11px] ${labelCls}`}>No dates found.</p>
              ) : (
                <div className="space-y-1.5">
                  {document.extracted_entities.dates.map((d, idx) => (
                    <div key={idx} className={`p-2 rounded border flex justify-between items-center text-[11px] ${rowCls}`}>
                      <span className="text-sky-300 font-bold">{d.value}</span>
                      <div className="flex items-center space-x-2">
                        <span className={`text-[10px] truncate max-w-xs ${labelCls}`}>{d.context}</span>
                        <span className={`px-1.5 rounded border text-[10px] text-sky-400 shrink-0 ${isDark ? 'bg-slate-900 border-slate-800' : 'bg-sky-50 border-sky-200'}`}>
                          p.{d.page || 1}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </section>

            <section className={sectionCls}>
              <div className="flex items-center space-x-1.5 text-purple-400 text-[11px] font-bold uppercase mb-2">
                <Users className="w-3.5 h-3.5" />
                <span>Parties ({document.extracted_entities.parties.length})</span>
              </div>
              {document.extracted_entities.parties.length === 0 ? (
                <p className={`text-[11px] ${labelCls}`}>No parties identified.</p>
              ) : (
                <div className="space-y-1.5">
                  {document.extracted_entities.parties.map((p, idx) => (
                    <div key={idx} className={`p-2 rounded border flex justify-between items-center text-[11px] ${rowCls}`}>
                      <div>
                        <span className={`font-bold mr-2 ${textCls}`}>{p.name}</span>
                        <span className="text-purple-400 text-[10px]">({p.role})</span>
                      </div>
                      <span className={`px-1.5 rounded border text-[10px] text-purple-400 shrink-0 ${isDark ? 'bg-slate-900 border-slate-800' : 'bg-purple-50 border-purple-200'}`}>
                        p.{p.page || 1}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </section>
          </div>
        )}

        {activeTab === 'domain_data' && (
          <div className="space-y-3 font-mono text-xs">
            <div className={`text-[11px] uppercase tracking-wider mb-1 ${labelCls}`}>
              {document.archetype} Schema
            </div>
            <div className={`p-3 rounded border space-y-2 overflow-x-auto ${isDark ? 'bg-slate-950 border-slate-800' : 'bg-slate-50 border-slate-200'}`}>
              <table className="w-full text-left border-collapse text-[11px]">
                <tbody>
                  {Object.entries(document.structured_data).map(([key, val]) => (
                    <tr key={key} className={`border-b ${rowHover}`}>
                      <td className="py-1.5 pr-4 text-sky-400 font-semibold align-top whitespace-nowrap">{key}</td>
                      <td className={`py-1.5 font-sans ${textCls}`}>
                        {typeof val === 'object' && val !== null ? (
                          <pre className={`font-mono text-[10px] p-2 rounded max-h-40 overflow-auto ${isDark ? 'bg-slate-900 text-slate-300' : 'bg-white text-slate-600 border border-slate-200'}`}>
                            {JSON.stringify(val, null, 2)}
                          </pre>
                        ) : (
                          String(val ?? '—')
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {activeTab === 'json' && (
          <div className="h-full">
            <pre className={`p-3 rounded font-mono text-[11px] overflow-auto max-h-[600px] leading-relaxed ${isDark ? 'bg-[#050810] border border-slate-800 text-sky-300' : 'bg-slate-50 border border-slate-200 text-slate-700'}`}>
              {JSON.stringify(document, null, 2)}
            </pre>
          </div>
        )}
      </div>
    </div>
  );
};
