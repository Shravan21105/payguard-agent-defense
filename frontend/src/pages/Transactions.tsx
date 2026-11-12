import React, { useEffect, useState } from 'react';
import { Search, RefreshCw, ArrowRightLeft } from 'lucide-react';
import { apiService } from '../services/api';
import type { TransactionRecord } from '../types';
import { Badge } from '../components/common/Badge';
import { RiskMeter } from '../components/common/RiskMeter';
import { PolicyPill } from '../components/common/PolicyPill';
import { Modal } from '../components/common/Modal';

export const Transactions: React.FC = () => {
  const [transactions, setTransactions] = useState<TransactionRecord[]>([]);
  const [filtered, setFiltered] = useState<TransactionRecord[]>([]);
  const [filterDecision, setFilterDecision] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [selectedTx, setSelectedTx] = useState<TransactionRecord | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  const fetchTransactions = async () => {
    setLoading(true);
    try {
      const data = await apiService.getTransactions(100);
      setTransactions(data);
      applyFilters(data, filterDecision, searchQuery);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTransactions();
  }, []);

  const applyFilters = (data: TransactionRecord[], decision: string, query: string) => {
    let result = [...data];
    if (decision !== 'ALL') {
      result = result.filter((t) => t.decision === decision);
    }
    if (query.trim()) {
      const q = query.toLowerCase();
      result = result.filter(
        (t) =>
          t.sender.toLowerCase().includes(q) ||
          t.recipient.toLowerCase().includes(q) ||
          t.transaction_id.toLowerCase().includes(q) ||
          (t.purpose && t.purpose.toLowerCase().includes(q))
      );
    }
    setFiltered(result);
  };

  const handleDecisionChange = (dec: string) => {
    setFilterDecision(dec);
    applyFilters(transactions, dec, searchQuery);
  };

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const q = e.target.value;
    setSearchQuery(q);
    applyFilters(transactions, filterDecision, q);
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-12">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
            <ArrowRightLeft className="w-6 h-6 text-emerald-400" />
            <span>Transaction Security Explorer</span>
          </h1>
          <p className="text-sm text-charcoal-400 mt-1">
            Historical audit log of evaluated autonomous agent transfers and enforcement decisions.
          </p>
        </div>

        <button
          onClick={fetchTransactions}
          className="flex items-center gap-2 px-3 py-2 rounded-lg bg-charcoal-900 border border-charcoal-750 hover:border-charcoal-600 text-xs font-mono text-charcoal-300 transition w-fit"
        >
          <RefreshCw className={`w-3.5 h-3.5 text-emerald-400 ${loading ? 'animate-spin' : ''}`} />
          <span>RELOAD TRANSACTIONS</span>
        </button>
      </div>

      {/* Filter and Search Bar */}
      <div className="payguard-panel p-4 flex flex-col md:flex-row md:items-center justify-between gap-4">
        {/* Search */}
        <div className="relative flex-1 max-w-md">
          <Search className="w-4 h-4 text-charcoal-400 absolute left-3 top-2.5" />
          <input
            type="text"
            placeholder="Search by account, tx hash, or intent..."
            value={searchQuery}
            onChange={handleSearchChange}
            className="w-full bg-charcoal-950 border border-charcoal-750 rounded-lg pl-9 pr-3 py-1.5 text-xs font-mono text-white placeholder-charcoal-400 focus:outline-none focus:border-emerald-500"
          />
        </div>

        {/* Decision Filter Tabs */}
        <div className="flex items-center gap-1.5 p-1 rounded-lg bg-charcoal-950 border border-charcoal-800 text-xs font-mono">
          {['ALL', 'ALLOW', 'WARN', 'BLOCK'].map((dec) => (
            <button
              key={dec}
              onClick={() => handleDecisionChange(dec)}
              className={`px-3 py-1 rounded-md transition ${
                filterDecision === dec
                  ? 'bg-charcoal-800 text-white font-bold border border-charcoal-700'
                  : 'text-charcoal-400 hover:text-white'
              }`}
            >
              {dec}
            </button>
          ))}
        </div>
      </div>

      {/* Transactions Table */}
      <div className="payguard-panel p-6">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono">
            <thead>
              <tr className="text-charcoal-400 border-b border-charcoal-800 pb-3">
                <th className="py-3 font-normal">TX ID</th>
                <th className="py-3 font-normal">DECISION</th>
                <th className="py-3 font-normal">SENDER</th>
                <th className="py-3 font-normal">RECIPIENT</th>
                <th className="py-3 font-normal">AMOUNT</th>
                <th className="py-3 font-normal">RISK SCORE</th>
                <th className="py-3 font-normal">APPROVAL</th>
                <th className="py-3 font-normal text-right">ACTION</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-charcoal-800/60">
              {filtered.length === 0 ? (
                <tr>
                  <td colSpan={8} className="py-12 text-center text-charcoal-400">
                    No transactions matching search criteria.
                  </td>
                </tr>
              ) : (
                filtered.map((tx) => (
                  <tr
                    key={tx.transaction_id}
                    onClick={() => setSelectedTx(tx)}
                    className="hover:bg-charcoal-850/50 cursor-pointer transition"
                  >
                    <td className="py-3 text-charcoal-400 truncate max-w-[100px]" title={tx.transaction_id}>
                      {tx.transaction_id}
                    </td>
                    <td className="py-3">
                      <Badge type={tx.decision} size="sm" />
                    </td>
                    <td className="py-3 text-charcoal-300 max-w-[140px] truncate" title={tx.sender}>
                      {tx.sender}
                    </td>
                    <td className="py-3 text-white max-w-[140px] truncate" title={tx.recipient}>
                      {tx.recipient}
                    </td>
                    <td className="py-3 text-emerald-400 font-bold">
                      {tx.amount.toFixed(2)} NEAR
                    </td>
                    <td className="py-3">
                      <RiskMeter score={tx.risk_score} />
                    </td>
                    <td className="py-3">
                      <span
                        className={`text-[11px] ${
                          tx.requires_approval
                            ? 'text-amber-400 font-bold'
                            : 'text-charcoal-400'
                        }`}
                      >
                        {tx.requires_approval ? 'REQUIRED' : 'AUTO'}
                      </span>
                    </td>
                    <td className="py-3 text-right">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          setSelectedTx(tx);
                        }}
                        className="px-2.5 py-1 rounded bg-charcoal-800 hover:bg-charcoal-700 text-charcoal-300 text-[11px]"
                      >
                        AUDIT
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Transaction Inspection Modal */}
      {selectedTx && (
        <Modal
          isOpen={!!selectedTx}
          onClose={() => setSelectedTx(null)}
          title={`Detailed Audit — ${selectedTx.transaction_id}`}
        >
          <div className="space-y-4">
            <div className="flex items-center justify-between p-3 rounded-lg bg-charcoal-850 border border-charcoal-750">
              <div>
                <span className="text-xs text-charcoal-400 block font-mono">VERDICT</span>
                <Badge type={selectedTx.decision} className="mt-1" />
              </div>
              <div className="text-right">
                <span className="text-xs text-charcoal-400 block font-mono">ASSESSED RISK</span>
                <div className="mt-1 flex items-center justify-end">
                  <RiskMeter score={selectedTx.risk_score} />
                </div>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3 text-xs font-mono">
              <div className="p-2.5 rounded bg-charcoal-850 border border-charcoal-800">
                <span className="text-charcoal-400 block">Sender</span>
                <span className="text-white font-bold truncate block">{selectedTx.sender}</span>
              </div>
              <div className="p-2.5 rounded bg-charcoal-850 border border-charcoal-800">
                <span className="text-charcoal-400 block">Recipient</span>
                <span className="text-white font-bold truncate block">{selectedTx.recipient}</span>
              </div>
              <div className="p-2.5 rounded bg-charcoal-850 border border-charcoal-800">
                <span className="text-charcoal-400 block">Amount</span>
                <span className="text-emerald-400 font-bold block">
                  {selectedTx.amount} {selectedTx.currency}
                </span>
              </div>
              <div className="p-2.5 rounded bg-charcoal-850 border border-charcoal-800">
                <span className="text-charcoal-400 block">Execution Permitted</span>
                <span className="text-white font-bold block">
                  {selectedTx.execution_allowed ? 'TRUE' : 'FALSE (HALTED)'}
                </span>
              </div>
            </div>

            {selectedTx.purpose && (
              <div className="p-2.5 rounded bg-charcoal-850 border border-charcoal-800 text-xs">
                <span className="text-charcoal-400 block font-mono mb-1">Agent Purpose</span>
                <span className="text-charcoal-200">{selectedTx.purpose}</span>
              </div>
            )}

            <div>
              <span className="text-xs font-mono uppercase text-charcoal-400 tracking-wider block mb-2">
                Deterministic Policy Outcomes
              </span>
              <div className="grid grid-cols-2 gap-2">
                {Object.entries(selectedTx.policy_checks).map(([name, status]) => (
                  <PolicyPill key={name} name={name} status={status} />
                ))}
              </div>
            </div>

            <div>
              <span className="text-xs font-mono uppercase text-charcoal-400 tracking-wider block mb-2">
                Enforcement Reasons
              </span>
              <div className="p-3 rounded bg-charcoal-850 border border-charcoal-800 space-y-1.5 text-xs text-charcoal-300">
                {selectedTx.reasons.map((reason, idx) => (
                  <div key={idx} className="flex items-start gap-2">
                    <span className="text-emerald-400 font-bold">•</span>
                    <span>{reason}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
};
