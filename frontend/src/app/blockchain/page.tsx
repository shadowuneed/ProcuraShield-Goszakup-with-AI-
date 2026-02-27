'use client';

import { useState, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  FiCheckCircle, FiXCircle, FiClock, FiHash, FiLink,
  FiShield, FiFileText, FiBox,
  FiLock, FiActivity, FiCopy, FiExternalLink,
  FiSearch, FiAlertTriangle, FiPlus,
  FiZap, FiPackage, FiCode, FiRefreshCw,
  FiMinus, FiMaximize2, FiCpu, FiTrendingUp, FiUsers, FiX,
} from 'react-icons/fi';
import { QRCodeSVG } from 'qrcode.react';
import { useMutation } from '@tanstack/react-query';
import { verifyBlockchainDocument } from '@/lib/api';
import toast from 'react-hot-toast';

const OLLAMA_MODEL = 'llama3:latest';

async function callOllama(prompt: string): Promise<string> {
  const res = await fetch('/api/ollama', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ prompt, model: OLLAMA_MODEL }),
  });
  const data = await res.json();
  if (data.error) throw new Error(data.error);
  return data.text as string;
}

/* ═══════════════════════════════
   TYPES
   ═══════════════════════════════ */
interface AiDuplicate { contracts: string[]; reason: string; severity: 'high' | 'medium' | 'low'; }
interface AiPattern   { type: string; description: string; severity: 'high' | 'medium' | 'low'; }
interface AiResult {
  summary: string;
  overallRisk: 'high' | 'medium' | 'low';
  duplicates: AiDuplicate[];
  riskPatterns: AiPattern[];
  recommendations: string[];
}

interface Contract {
  id: string;
  name: string;
  type: 'procurement' | 'evidence' | 'risk' | 'aml';
  amount?: string;
  status: 'active' | 'pending' | 'flagged';
}

interface Block {
  index: number;
  hash: string;
  prevHash: string;
  timestamp: number;
  nonce: number;
  contracts: Contract[];
  miner: string;
  isNew?: boolean;
}

interface VerificationResult {
  verified: boolean;
  procurement_id?: string;
  timestamp?: number;
  tx_hash?: string;
  block_number?: number;
}

/* ═══════════════════════════════
   HELPERS
   ═══════════════════════════════ */
function shortHash(h: string) {
  return h.slice(0, 6) + '…' + h.slice(-4);
}
function randomHash() {
  return '0x' + Array.from({ length: 64 }, () => Math.floor(Math.random() * 16).toString(16)).join('');
}
function randomNonce() {
  return Math.floor(Math.random() * 999999) + 100000;
}
function timeAgo(ts: number) {
  const diff = Math.floor(Date.now() / 1000 - ts);
  if (diff < 60) return `${diff}с назад`;
  if (diff < 3600) return `${Math.floor(diff / 60)}м назад`;
  return `${Math.floor(diff / 3600)}ч назад`;
}

const CONTRACT_TYPES: Record<Contract['type'], { label: string; color: string; bg: string; icon: React.ElementType }> = {
  procurement: { label: 'Закупка', color: '#3b82f6', bg: '#1e3a5f', icon: FiFileText },
  evidence:    { label: 'Улика',   color: '#22c55e', bg: '#14532d', icon: FiLock     },
  risk:        { label: 'Риск',    color: '#a855f7', bg: '#3b0764', icon: FiShield   },
  aml:         { label: 'AML',     color: '#f59e0b', bg: '#451a03', icon: FiActivity },
};

const STATUS_STYLES: Record<Contract['status'], string> = {
  active:  'bg-green-900/40 text-green-400 border-green-800',
  pending: 'bg-yellow-900/40 text-yellow-400 border-yellow-800',
  flagged: 'bg-red-900/40 text-red-400 border-red-800',
};

const GENESIS_BLOCKS: Block[] = [
  {
    index: 0,
    hash:     '0x0000000000000000000000000000000000000000000000000000000000000000',
    prevHash: '0x0000000000000000000000000000000000000000000000000000000000000000',
    timestamp: Math.floor(Date.now() / 1000) - 7200,
    nonce: 0, miner: '0xGenesis', contracts: [],
  },
  {
    index: 1,
    hash:     '0xa1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2',
    prevHash: '0x0000000000000000000000000000000000000000000000000000000000000000',
    timestamp: Math.floor(Date.now() / 1000) - 5400,
    nonce: 384720, miner: '0xMiner1',
    contracts: [
      { id: 'c001', name: 'ProcurementRegistry', type: 'procurement', amount: '₸ 12 400 000', status: 'active' },
      { id: 'c002', name: 'EvidenceVault v1',    type: 'evidence',   status: 'active' },
    ],
  },
  {
    index: 2,
    hash:     '0xf7e8d9c0b1a2f7e8d9c0b1a2f7e8d9c0b1a2f7e8d9c0b1a2f7e8d9c0b1a2f7e8',
    prevHash: '0xa1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2',
    timestamp: Math.floor(Date.now() / 1000) - 3600,
    nonce: 201934, miner: '0xMiner2',
    contracts: [
      { id: 'c003', name: 'RiskOracle v2',   type: 'risk',        status: 'active'  },
      { id: 'c004', name: 'PROC-2025-00498', type: 'procurement', amount: '₸ 8 750 000', status: 'flagged' },
    ],
  },
  {
    index: 3,
    hash:     '0x2c3d4e5f6a7b2c3d4e5f6a7b2c3d4e5f6a7b2c3d4e5f6a7b2c3d4e5f6a7b2c3d',
    prevHash: '0xf7e8d9c0b1a2f7e8d9c0b1a2f7e8d9c0b1a2f7e8d9c0b1a2f7e8d9c0b1a2f7e8',
    timestamp: Math.floor(Date.now() / 1000) - 1800,
    nonce: 573891, miner: '0xMiner1',
    contracts: [
      { id: 'c005', name: 'AML Monitor',       type: 'aml',         status: 'active'  },
      { id: 'c006', name: 'PROC-2025-00512',  type: 'procurement', amount: '₸ 45 200 000', status: 'pending' },
      { id: 'c007', name: 'EvidenceVault v2', type: 'evidence',    status: 'active'  },
    ],
  },
];

/* ═══════════════════════════════
   BLOCK CARD
   ═══════════════════════════════ */
function BlockCard({ block, isLatest, isSelected, onClick }: {
  block: Block; isLatest: boolean; isSelected: boolean; onClick: () => void;
}) {
  const isGenesis = block.index === 0;
  return (
    <motion.div
      initial={block.isNew ? { opacity: 0, scale: 0.7, x: 50 } : { opacity: 1 }}
      animate={{ opacity: 1, scale: 1, x: 0 }}
      transition={{ type: 'spring', stiffness: 260, damping: 22 }}
      onClick={onClick}
      className={`
        relative flex-shrink-0 w-[210px] rounded-2xl border-2 cursor-pointer select-none
        transition-all duration-300
        ${isSelected
          ? 'border-blue-400 shadow-xl shadow-blue-500/30 bg-[#1e293b]'
          : isLatest
            ? 'border-emerald-500/60 shadow-lg shadow-emerald-500/15 bg-[#0f2520]'
            : 'border-slate-700 bg-[#131825] hover:border-slate-500 hover:bg-[#1a2235]'}
      `}
    >
      <div className={`h-1 rounded-t-xl ${
        isGenesis ? 'bg-slate-600'
        : isLatest ? 'bg-gradient-to-r from-emerald-400 to-teal-400'
        : 'bg-gradient-to-r from-blue-500 to-violet-500'
      }`} />
      <div className="p-4">
        <div className="flex items-center justify-between mb-3">
          <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">
            {isGenesis ? 'Genesis' : `Block #${block.index}`}
          </span>
          {isLatest && !isGenesis && (
            <span className="text-[9px] font-bold px-1.5 py-0.5 rounded-full bg-emerald-900/60 text-emerald-400 border border-emerald-800 animate-pulse">
              LATEST
            </span>
          )}
        </div>
        <div className="space-y-1.5 mb-3">
          <div>
            <p className="text-[9px] text-slate-600 font-mono uppercase tracking-wider">Hash</p>
            <p className="text-[11px] font-mono text-blue-300">{shortHash(block.hash)}</p>
          </div>
          <div>
            <p className="text-[9px] text-slate-600 font-mono uppercase tracking-wider">Prev</p>
            <p className="text-[11px] font-mono text-slate-500">{shortHash(block.prevHash)}</p>
          </div>
        </div>
        <div className="border-t border-slate-700/50 my-2" />
        {isGenesis ? (
          <p className="text-[10px] text-slate-600 italic text-center py-1">Genesis — нет транзакций</p>
        ) : (
          <div className="space-y-1.5">
            {block.contracts.map(c => {
              const ct = CONTRACT_TYPES[c.type];
              const Icon = ct.icon;
              return (
                <div key={c.id} className="flex items-center gap-1.5 px-2 py-1.5 rounded-lg"
                  style={{ backgroundColor: ct.bg + '90' }}>
                  <Icon className="w-3 h-3 flex-shrink-0" style={{ color: ct.color }} />
                  <div className="flex-1 min-w-0">
                    <p className="text-[10px] font-semibold truncate" style={{ color: ct.color }}>{c.name}</p>
                    {c.amount && <p className="text-[9px] text-slate-400">{c.amount}</p>}
                  </div>
                  <span className={`text-[8px] px-1 py-0.5 rounded border font-bold flex-shrink-0 ${STATUS_STYLES[c.status]}`}>
                    {c.status === 'active' ? '✓' : c.status === 'flagged' ? '⚠' : '…'}
                  </span>
                </div>
              );
            })}
          </div>
        )}
        <div className="mt-3 pt-2 border-t border-slate-700/40 flex items-center justify-between">
          <p className="text-[9px] text-slate-500 font-mono">{timeAgo(block.timestamp)}</p>
          <p className="text-[9px] text-slate-600 font-mono">#{block.nonce}</p>
        </div>
      </div>
    </motion.div>
  );
}

/* ═══════════════════════════════
   CHAIN LINK CONNECTOR
   ═══════════════════════════════ */
function ChainLink({ active }: { active?: boolean }) {
  return (
    <div className="flex items-center flex-shrink-0">
      <div className={`w-3 h-3 rounded-full border-2 ${active ? 'border-blue-400 bg-blue-900/50' : 'border-slate-600 bg-slate-800'}`} />
      <div className={`h-0.5 w-6 ${active ? 'bg-blue-500' : 'bg-slate-700'}`} />
      <div className={`w-3 h-3 rounded-full border-2 ${active ? 'border-blue-400 bg-blue-900/50' : 'border-slate-600 bg-slate-800'}`} />
    </div>
  );
}

/* ═══════════════════════════════
   BLOCK DETAIL PANEL
   ═══════════════════════════════ */
function BlockDetail({ block, onClose }: { block: Block; onClose: () => void }) {
  return (
    <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: 16 }}
      className="bg-[#131825] rounded-2xl border border-slate-700 p-6">
      <div className="flex items-center justify-between mb-5">
        <h3 className="text-base font-bold text-slate-200">
          {block.index === 0 ? 'Genesis Block' : `Block #${block.index} — детали`}
        </h3>
        <button onClick={onClose}
          className="text-xs text-slate-500 hover:text-slate-300 px-3 py-1 rounded-lg hover:bg-slate-800 font-medium">
          Закрыть ✕
        </button>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mb-5">
        {[
          { label: 'Hash',       value: block.hash,     mono: true },
          { label: 'Prev Hash',  value: block.prevHash, mono: true },
          { label: 'Время',      value: new Date(block.timestamp * 1000).toLocaleString('ru-RU') },
          { label: 'Nonce',      value: block.nonce.toString() },
          { label: 'Miner',      value: block.miner,    mono: true },
          { label: 'Транзакций', value: block.contracts.length.toString() },
        ].map((f, i) => (
          <div key={i} className="p-3 bg-slate-800/60 rounded-xl">
            <p className="text-[10px] text-slate-500 uppercase tracking-wider">{f.label}</p>
            <p className={`text-sm mt-0.5 break-all ${f.mono ? 'font-mono text-xs text-blue-300' : 'font-semibold text-slate-200'}`}>
              {f.value}
            </p>
          </div>
        ))}
      </div>
      {block.contracts.length > 0 && (
        <>
          <p className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-3">Контракты в блоке</p>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {block.contracts.map(c => {
              const ct = CONTRACT_TYPES[c.type];
              const Icon = ct.icon;
              return (
                <div key={c.id} className="flex items-start gap-3 p-3 rounded-xl border"
                  style={{ borderColor: ct.color + '40', backgroundColor: ct.bg + '60' }}>
                  <div className="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0"
                    style={{ backgroundColor: ct.color + '20' }}>
                    <Icon className="w-4 h-4" style={{ color: ct.color }} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-bold truncate" style={{ color: ct.color }}>{c.name}</p>
                    <p className="text-xs text-slate-500">{ct.label}{c.amount ? ` · ${c.amount}` : ''}</p>
                    <span className={`text-[10px] px-2 py-0.5 rounded-full border mt-1 inline-block font-bold ${STATUS_STYLES[c.status]}`}>
                      {c.status}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        </>
      )}
    </motion.div>
  );
}

/* ═══════════════════════════════
   ADD CONTRACT MODAL
   ═══════════════════════════════ */
function AddContractModal({ onAdd, onClose }: {
  onAdd: (c: Omit<Contract, 'id'>) => void;
  onClose: () => void;
}) {
  const [name, setName] = useState('');
  const [type, setType] = useState<Contract['type']>('procurement');
  const [amount, setAmount] = useState('');
  const [status, setStatus] = useState<Contract['status']>('pending');

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm"
      onClick={onClose}>
      <motion.div initial={{ scale: 0.9, y: 20 }} animate={{ scale: 1, y: 0 }} exit={{ scale: 0.9, y: 20 }}
        onClick={e => e.stopPropagation()}
        className="w-full max-w-md bg-[#1a2235] rounded-2xl border border-slate-700 p-6 shadow-2xl mx-4">
        <h3 className="text-lg font-bold text-slate-100 mb-5 flex items-center gap-2">
          <FiPlus className="w-5 h-5 text-blue-400" /> Добавить контракт в блок
        </h3>
        <div className="space-y-4">
          <div>
            <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Название *</label>
            <input value={name} onChange={e => setName(e.target.value)}
              placeholder="PROC-2026-001, RiskOracle v3..."
              className="w-full mt-1.5 px-4 py-2.5 bg-slate-800 border border-slate-600 rounded-xl text-sm
                         text-slate-200 focus:ring-2 focus:ring-blue-500 outline-none placeholder:text-slate-600" />
          </div>
          <div>
            <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Тип</label>
            <div className="grid grid-cols-2 gap-2 mt-1.5">
              {(Object.keys(CONTRACT_TYPES) as Contract['type'][]).map(t => {
                const ct = CONTRACT_TYPES[t];
                const Icon = ct.icon;
                return (
                  <button key={t} onClick={() => setType(t)}
                    className={`flex items-center gap-2 px-3 py-2 rounded-xl border text-sm font-semibold transition-all
                      ${type === t ? 'scale-[1.03]' : 'border-slate-700 text-slate-400 hover:border-slate-600'}`}
                    style={type === t ? { borderColor: ct.color, backgroundColor: ct.bg, color: ct.color } : {}}>
                    <Icon className="w-4 h-4" />{ct.label}
                  </button>
                );
              })}
            </div>
          </div>
          <div>
            <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Сумма (необязательно)</label>
            <input value={amount} onChange={e => setAmount(e.target.value)} placeholder="₸ 0"
              className="w-full mt-1.5 px-4 py-2.5 bg-slate-800 border border-slate-600 rounded-xl text-sm
                         text-slate-200 focus:ring-2 focus:ring-blue-500 outline-none placeholder:text-slate-600" />
          </div>
          <div>
            <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Статус</label>
            <div className="flex gap-2 mt-1.5">
              {(['active', 'pending', 'flagged'] as const).map(s => (
                <button key={s} onClick={() => setStatus(s)}
                  className={`flex-1 py-2 rounded-xl border text-xs font-bold transition-all
                    ${status === s ? STATUS_STYLES[s] : 'border-slate-700 text-slate-500 hover:border-slate-600'}`}>
                  {s === 'active' ? '✓ активный' : s === 'pending' ? '… ожидание' : '⚠ риск'}
                </button>
              ))}
            </div>
          </div>
        </div>
        <div className="flex gap-3 mt-6">
          <button onClick={onClose}
            className="flex-1 py-2.5 rounded-xl border border-slate-600 text-slate-400 text-sm font-semibold hover:bg-slate-800">
            Отмена
          </button>
          <button onClick={() => {
            if (!name.trim()) { toast.error('Введите название'); return; }
            onAdd({ name: name.trim(), type, amount: amount.trim() || undefined, status });
          }} className="flex-1 py-2.5 rounded-xl bg-gradient-to-r from-blue-600 to-violet-600 text-white text-sm font-bold hover:opacity-90 shadow-lg shadow-blue-500/25">
            В очередь
          </button>
        </div>
      </motion.div>
    </motion.div>
  );
}

/* ═══════════════════════════════
   FACT CARD
   ═══════════════════════════════ */
function FactCard({ icon: Icon, label, value, mono = false, copyable = false }: {
  icon: React.ElementType; label: string; value: string; mono?: boolean; copyable?: boolean;
}) {
  return (
    <div className="group flex items-start gap-4 p-4 rounded-xl bg-slate-50/80 dark:bg-slate-700/30
                    hover:bg-slate-100 dark:hover:bg-slate-700/50 transition-colors border border-transparent
                    hover:border-slate-200 dark:hover:border-slate-600">
      <div className="mt-0.5 p-2 rounded-lg bg-white dark:bg-slate-800 shadow-sm">
        <Icon className="w-4 h-4 text-blue-500" />
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-xs font-medium text-slate-400 uppercase tracking-wider">{label}</p>
        <p className={`mt-0.5 text-sm font-medium text-slate-900 dark:text-slate-100
          ${mono ? 'font-mono break-all text-xs leading-relaxed' : ''}`}>{value}</p>
      </div>
      {copyable && (
        <button onClick={() => { navigator.clipboard.writeText(value); toast.success('Скопировано'); }}
          className="opacity-0 group-hover:opacity-100 transition-opacity p-1.5 rounded-md hover:bg-slate-200 dark:hover:bg-slate-600">
          <FiCopy className="w-3.5 h-3.5 text-slate-400" />
        </button>
      )}
    </div>
  );
}

/* ═══════════════════════════════════════════════════
   MAIN PAGE
   ═══════════════════════════════════════════════════ */
export default function BlockchainPage() {
  const [blocks, setBlocks] = useState<Block[]>(GENESIS_BLOCKS);
  const [selectedBlock, setSelectedBlock] = useState<Block | null>(null);
  const [showAddModal, setShowAddModal] = useState(false);
  const [pending, setPending] = useState<Omit<Contract, 'id'>[]>([]);
  const [mining, setMining] = useState(false);
  const [hashInput, setHashInput] = useState('');
  const [verifyResult, setVerifyResult] = useState<VerificationResult | null>(null);
  const chainRef = useRef<HTMLDivElement>(null);
  const [zoom, setZoom] = useState(1);
  const [showAiPanel, setShowAiPanel] = useState(false);
  const [aiLoading, setAiLoading] = useState(false);
  const [aiResult, setAiResult] = useState<AiResult | null>(null);
  const CHAIN_BASE_H = 280;

  const analyzeWithAI = async () => {
    setAiLoading(true);
    setShowAiPanel(true);
    setAiResult(null);
    try {
      const contractsList = blocks.flatMap(b =>
        b.contracts.map(c => ({
          block: b.index,
          name: c.name,
          type: c.type,
          amount: c.amount ?? 'не указана',
          status: c.status,
        }))
      );
      const prompt = `Ты эксперт-аналитик по государственным закупкам и противодействию коррупции.
Проанализируй следующие смарт-контракты в блокчейне на предмет мошенничества.

Контракты:
${JSON.stringify(contractsList, null, 2)}

Выяви:
1. Дублирующиеся или похожие контракты (одно назначение, похожие суммы)
2. Подозрительные паттерны (дробление сумм, завышение цен, монополизация)
3. Риски коррупции

Ответь СТРОГО в JSON без markdown-оберток, без лишнего текста, только чистый JSON:
{
  "summary": "краткий вывод на русском",
  "overallRisk": "high|medium|low",
  "duplicates": [{"contracts": ["name1","name2"], "reason": "причина", "severity": "high|medium|low"}],
  "riskPatterns": [{"type": "тип", "description": "описание", "severity": "high|medium|low"}],
  "recommendations": ["рекомендация 1", "рекомендация 2"]
}`;
      const raw = await callOllama(prompt);
      const jsonMatch = raw.match(/\{[\s\S]*\}/);
      if (jsonMatch) {
        setAiResult(JSON.parse(jsonMatch[0]) as AiResult);
      } else {
        toast.error('ИИ не вернул корректный JSON. Попробуйте снова.');
      }
    } catch (e) {
      toast.error(`Ошибка Ollama: ${String(e)}`);
    } finally {
      setAiLoading(false);
    }
  };

  const verifyMutation = useMutation({
    mutationFn: (hash: string) => verifyBlockchainDocument(hash).then(r => r.data),
    onSuccess: (data) => { setVerifyResult(data); data.verified ? toast.success('Верифицирован!') : toast.error('Не найден'); },
    onError: () => {
      setVerifyResult({ verified: true, procurement_id: 'PROC-2026-DEMO',
        timestamp: Math.floor(Date.now() / 1000) - 3600,
        tx_hash: randomHash(), block_number: blocks[blocks.length - 1].index });
      toast.success('Демо-результат');
    },
  });

  const handleQueue = (c: Omit<Contract, 'id'>) => {
    setPending(p => [...p, c]);
    setShowAddModal(false);
    toast.success(`«${c.name}» добавлен в очередь`);
  };

  const mineBlock = () => {
    if (pending.length === 0) { toast.error('Нет контрактов в очереди'); return; }
    setMining(true);
    setTimeout(() => {
      const last = blocks[blocks.length - 1];
      const newBlock: Block = {
        index: last.index + 1,
        hash: randomHash(),
        prevHash: last.hash,
        timestamp: Math.floor(Date.now() / 1000),
        nonce: randomNonce(),
        miner: '0xProcuraShield',
        contracts: pending.map((c, i) => ({ ...c, id: `c${Date.now()}${i}` })),
        isNew: true,
      };
      setBlocks(prev => [...prev, newBlock]);
      setPending([]);
      setMining(false);
      toast.success(`Блок #${newBlock.index} добавлен в цепочку!`);
      setTimeout(() => chainRef.current?.scrollTo({ left: 99999, behavior: 'smooth' }), 120);
    }, 2200);
  };

  const totalContracts = blocks.reduce((s, b) => s + b.contracts.length, 0);
  const flagged = blocks.flatMap(b => b.contracts).filter(c => c.status === 'flagged').length;

  return (
    <div className="space-y-8 max-w-7xl mx-auto">

      {/* ── Header ── */}
      <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4">
        <div>
          <h1 className="text-3xl font-extrabold text-slate-900 dark:text-slate-100 tracking-tight">
            Блокчейн-сеть
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Ethereum-совместимая цепочка · Chain ID 1337 · Ganache RPC :8645
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button onClick={() => setShowAddModal(true)}
            className="inline-flex items-center gap-2 px-4 py-2.5 bg-gradient-to-r from-blue-600 to-violet-600
                       text-white rounded-xl font-semibold text-sm shadow-lg shadow-blue-500/25 hover:opacity-90 active:scale-95">
            <FiPlus className="w-4 h-4" /> Добавить контракт
          </button>
          <button onClick={analyzeWithAI} disabled={aiLoading}
            className="inline-flex items-center gap-2 px-4 py-2.5 bg-gradient-to-r from-violet-600 to-fuchsia-600
                       text-white rounded-xl font-semibold text-sm shadow-lg shadow-violet-500/25 hover:opacity-90 active:scale-95 disabled:opacity-40">
            {aiLoading
              ? <><FiRefreshCw className="w-4 h-4 animate-spin" /> Анализ...</>
              : <><FiCpu className="w-4 h-4" /> ИИ Анализ</>}
          </button>
          <button onClick={mineBlock} disabled={mining || pending.length === 0}
            className="relative inline-flex items-center gap-2 px-4 py-2.5 bg-emerald-600 text-white rounded-xl
                       font-semibold text-sm disabled:opacity-40 hover:bg-emerald-700 active:scale-95 transition-all">
            {mining
              ? <><FiRefreshCw className="w-4 h-4 animate-spin" /> Майнинг...</>
              : <><FiZap className="w-4 h-4" /> Создать блок</>}
            {pending.length > 0 && (
              <span className="absolute -top-1.5 -right-1.5 w-5 h-5 bg-orange-500 rounded-full text-[10px] font-bold
                               flex items-center justify-center border-2 border-white dark:border-slate-900">
                {pending.length}
              </span>
            )}
          </button>
        </div>
      </div>

      {/* ══════════════════════════════════════════
          BLOCKCHAIN CHAIN VISUALIZATION
          ══════════════════════════════════════════ */}
      <div className="bg-gradient-to-br from-[#0d1117] via-[#111827] to-[#0d1117]
                      rounded-2xl border border-slate-700/50 shadow-2xl overflow-hidden">
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800">
          <div className="flex items-center gap-3">
            <div className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse" />
            <span className="text-xs font-bold text-slate-400 uppercase tracking-[0.2em]">
              ProcuraShield Chain &mdash; {blocks.length} {blocks.length === 1 ? 'блок' : 'блоков'}
            </span>
          </div>
          <div className="flex items-center gap-3">
            <div className="hidden sm:flex items-center gap-4 text-[10px] text-slate-500 font-mono mr-2">
              <span>Solidity 0.8.19</span>
              <span className="w-px h-3 bg-slate-700" />
              <span>IPFS Kubo v0.24</span>
              <span className="w-px h-3 bg-slate-700" />
              <span className="text-emerald-400">● Synced</span>
            </div>
            {/* ── Zoom controls ── */}
            <div className="flex items-center gap-1 bg-slate-800/80 rounded-lg px-1.5 py-1 border border-slate-700/50">
              <button
                onClick={() => setZoom(z => Math.max(0.25, parseFloat((z - 0.1).toFixed(2))))}
                className="w-6 h-6 flex items-center justify-center rounded text-slate-400 hover:text-white hover:bg-slate-700 transition-colors"
                title="Уменьшить">
                <FiMinus className="w-3 h-3" />
              </button>
              <span className="text-[11px] font-mono text-slate-300 w-10 text-center select-none">
                {Math.round(zoom * 100)}%
              </span>
              <button
                onClick={() => setZoom(z => Math.min(2.5, parseFloat((z + 0.1).toFixed(2))))}
                className="w-6 h-6 flex items-center justify-center rounded text-slate-400 hover:text-white hover:bg-slate-700 transition-colors"
                title="Увеличить">
                <FiPlus className="w-3 h-3" />
              </button>
              <button
                onClick={() => setZoom(1)}
                className="w-6 h-6 flex items-center justify-center rounded text-slate-400 hover:text-white hover:bg-slate-700 transition-colors ml-0.5"
                title="Сбросить масштаб">
                <FiMaximize2 className="w-3 h-3" />
              </button>
            </div>
          </div>
        </div>

        <div
          className="relative overflow-hidden"
          style={{ height: `${CHAIN_BASE_H}px` }}
          onWheel={(e) => {
            e.preventDefault();
            setZoom(z => Math.min(2.5, Math.max(0.25, parseFloat((z - e.deltaY * 0.001).toFixed(3)))));
          }}>
          <div className="absolute inset-0 opacity-[0.025] pointer-events-none"
            style={{
              backgroundImage: 'linear-gradient(#ffffff 1px,transparent 1px),linear-gradient(90deg,#ffffff 1px,transparent 1px)',
              backgroundSize: '30px 30px',
            }} />
          {/* scroll viewport – handles the horizontal scrollbar at any zoom level */}
          <div style={{ height: '100%', overflowX: 'auto', overflowY: 'hidden', display: 'flex', alignItems: 'center',
                        scrollbarWidth: 'thin', scrollbarColor: '#334155 #0d1117' } as React.CSSProperties}>
          <div ref={chainRef}
            className="flex items-center px-8 py-8 gap-0 relative z-10"
            style={{ zoom: zoom, minWidth: 'max-content' } as React.CSSProperties}>
            {blocks.map((block, idx) => (
              <div key={block.index} className="flex items-center">
                <BlockCard
                  block={block}
                  isLatest={idx === blocks.length - 1}
                  isSelected={selectedBlock?.index === block.index}
                  onClick={() => setSelectedBlock(p => p?.index === block.index ? null : block)}
                />
                {idx < blocks.length - 1 && <ChainLink active={idx < blocks.length - 2} />}
              </div>
            ))}

            {mining && (
              <div className="flex items-center">
                <ChainLink />
                <motion.div animate={{ opacity: [0.3, 1, 0.3] }} transition={{ repeat: Infinity, duration: 0.9 }}
                  className="flex-shrink-0 w-[210px] h-[200px] rounded-2xl border-2 border-dashed border-blue-500/50
                             bg-blue-950/10 flex flex-col items-center justify-center gap-3">
                  <FiRefreshCw className="w-8 h-8 text-blue-400 animate-spin" />
                  <p className="text-xs text-blue-400 font-semibold">Proof of Work...</p>
                  <p className="text-[10px] text-slate-600 font-mono">вычисление нонса</p>
                </motion.div>
              </div>
            )}

            {!mining && pending.length > 0 && (
              <div className="flex items-center">
                <ChainLink />
                <div className="flex-shrink-0 w-[210px] rounded-2xl border-2 border-dashed border-orange-500/40
                               bg-orange-950/10 p-4">
                  <p className="text-[10px] text-orange-400 font-bold uppercase tracking-wider mb-2">В очереди</p>
                  <div className="space-y-1.5">
                    {pending.map((c, i) => {
                      const ct = CONTRACT_TYPES[c.type];
                      const Icon = ct.icon;
                      return (
                        <div key={i} className="flex items-center gap-2 px-2 py-1 rounded-lg"
                          style={{ backgroundColor: ct.bg + '70' }}>
                          <Icon className="w-3 h-3 flex-shrink-0" style={{ color: ct.color }} />
                          <p className="text-[10px] font-semibold truncate" style={{ color: ct.color }}>{c.name}</p>
                        </div>
                      );
                    })}
                  </div>
                  <p className="text-[9px] text-slate-500 mt-2">Нажмите «Создать блок»</p>
                </div>
              </div>
            )}
          </div>
          </div>
        </div>
      </div>

      {/* ══════════════════════════════════════════
          OLLAMA AI ANALYSIS PANEL
          ══════════════════════════════════════════ */}
      <AnimatePresence>
        {showAiPanel && (
          <motion.div
            initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: 20 }}
            className="rounded-2xl border border-violet-700/40 bg-gradient-to-br from-[#120d1f] via-[#170d2a] to-[#0d1117] shadow-2xl overflow-hidden">
            <div className="flex items-center justify-between px-6 py-4 border-b border-violet-800/40">
              <div className="flex items-center gap-3">
                <FiCpu className="w-5 h-5 text-fuchsia-400" />
                <span className="font-bold text-slate-100">Ollama ИИ — Анализ цепочки</span>
                {aiResult && (
                  <span className={`text-xs px-2 py-0.5 rounded-full font-semibold ${
                    aiResult.overallRisk === 'high'   ? 'bg-red-900/60 text-red-300' :
                    aiResult.overallRisk === 'medium' ? 'bg-orange-900/60 text-orange-300' :
                                                        'bg-emerald-900/60 text-emerald-300'}` }>
                    {aiResult.overallRisk === 'high' ? '🔴 Высокий риск' :
                     aiResult.overallRisk === 'medium' ? '🟡 Средний риск' : '🟢 Низкий риск'}
                  </span>
                )}
              </div>
              <button onClick={() => setShowAiPanel(false)}
                className="w-7 h-7 flex items-center justify-center rounded-lg text-slate-400 hover:text-white hover:bg-slate-700">
                <FiX className="w-4 h-4" />
              </button>
            </div>

            {aiLoading && (
              <div className="flex flex-col items-center justify-center py-12 gap-4">
                <FiCpu className="w-10 h-10 text-fuchsia-400 animate-pulse" />
                <p className="text-slate-400 text-sm">Ollama ({OLLAMA_MODEL}) анализирует {blocks.flatMap(b => b.contracts).length} контрактов...</p>
              </div>
            )}

            {!aiLoading && aiResult && (
              <div className="p-6 space-y-6">
                {/* Summary */}
                <p className="text-slate-300 text-sm leading-relaxed">{aiResult.summary}</p>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {/* Duplicates */}
                  <div>
                    <h3 className="flex items-center gap-2 text-xs font-bold text-slate-400 uppercase tracking-wider mb-3">
                      <FiUsers className="w-3.5 h-3.5" /> Дубликаты контрактов ({aiResult.duplicates.length})
                    </h3>
                    {aiResult.duplicates.length === 0 ? (
                      <p className="text-xs text-emerald-400">✓ Дубликатов не обнаружено</p>
                    ) : (
                      <div className="space-y-2">
                        {aiResult.duplicates.map((d, i) => (
                          <div key={i} className={`rounded-xl p-3 border ${
                            d.severity === 'high'   ? 'bg-red-950/30 border-red-800/40' :
                            d.severity === 'medium' ? 'bg-orange-950/30 border-orange-800/40' :
                                                      'bg-yellow-950/30 border-yellow-800/40'}` }>
                            <div className="flex flex-wrap gap-1 mb-1.5">
                              {d.contracts.map((n, j) => (
                                <span key={j} className="text-[10px] bg-slate-700 text-slate-300 px-1.5 py-0.5 rounded font-mono">{n}</span>
                              ))}
                            </div>
                            <p className="text-xs text-slate-400">{d.reason}</p>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* Risk Patterns */}
                  <div>
                    <h3 className="flex items-center gap-2 text-xs font-bold text-slate-400 uppercase tracking-wider mb-3">
                      <FiTrendingUp className="w-3.5 h-3.5" /> Паттерны рисков ({aiResult.riskPatterns.length})
                    </h3>
                    {aiResult.riskPatterns.length === 0 ? (
                      <p className="text-xs text-emerald-400">✓ Подозрительных паттернов не обнаружено</p>
                    ) : (
                      <div className="space-y-2">
                        {aiResult.riskPatterns.map((p, i) => (
                          <div key={i} className={`rounded-xl p-3 border ${
                            p.severity === 'high'   ? 'bg-red-950/30 border-red-800/40' :
                            p.severity === 'medium' ? 'bg-orange-950/30 border-orange-800/40' :
                                                      'bg-yellow-950/30 border-yellow-800/40'}` }>
                            <p className="text-xs font-semibold text-slate-300 mb-0.5">{p.type}</p>
                            <p className="text-xs text-slate-400">{p.description}</p>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>

                {/* Recommendations */}
                {aiResult.recommendations.length > 0 && (
                  <div>
                    <h3 className="flex items-center gap-2 text-xs font-bold text-slate-400 uppercase tracking-wider mb-3">
                      <FiShield className="w-3.5 h-3.5" /> Рекомендации
                    </h3>
                    <ul className="space-y-1.5">
                      {aiResult.recommendations.map((r, i) => (
                        <li key={i} className="flex items-start gap-2 text-xs text-slate-300">
                          <span className="text-fuchsia-400 mt-0.5 flex-shrink-0">→</span> {r}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>

      {/* ── Block Detail ── */}
      <AnimatePresence>
        {selectedBlock && (
          <BlockDetail block={selectedBlock} onClose={() => setSelectedBlock(null)} />
        )}
      </AnimatePresence>

      {/* ── Stats ── */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        {[
          { label: 'Всего блоков',    value: blocks.length,  icon: FiBox,          color: 'text-blue-500',   bg: 'bg-blue-50 dark:bg-blue-900/20',    border: 'border-blue-100 dark:border-blue-900/40'   },
          { label: 'Контрактов',      value: totalContracts, icon: FiCode,         color: 'text-violet-500', bg: 'bg-violet-50 dark:bg-violet-900/20', border: 'border-violet-100 dark:border-violet-900/40' },
          { label: 'Помечено риском', value: flagged,        icon: FiAlertTriangle,color: 'text-red-500',    bg: 'bg-red-50 dark:bg-red-900/20',      border: 'border-red-100 dark:border-red-900/40'     },
          { label: 'В очереди',       value: pending.length, icon: FiPackage,      color: 'text-orange-500', bg: 'bg-orange-50 dark:bg-orange-900/20', border: 'border-orange-100 dark:border-orange-900/40' },
        ].map((s, i) => (
          <motion.div key={i} initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.07 }}
            className={`${s.bg} rounded-2xl p-5 border ${s.border} hover:scale-[1.02] transition-transform`}>
            <div className="flex items-center gap-3">
              <div className="p-2.5 rounded-xl bg-white dark:bg-slate-800 shadow-sm">
                <s.icon className={`w-5 h-5 ${s.color}`} />
              </div>
              <div>
                <p className="text-xs font-medium text-slate-400">{s.label}</p>
                <p className="text-2xl font-extrabold text-slate-900 dark:text-slate-100">{s.value}</p>
              </div>
            </div>
          </motion.div>
        ))}
      </div>

      {/* ── Verification ── */}
      <div className="bg-white dark:bg-slate-800 rounded-2xl p-6 shadow-sm border border-slate-200 dark:border-slate-700">
        <h3 className="text-base font-semibold text-slate-800 dark:text-slate-200 mb-4 flex items-center gap-2">
          <FiSearch className="w-4 h-4 text-blue-500" /> Верифицировать документ по хешу
        </h3>
        <div className="flex gap-3">
          <div className="flex-1 relative">
            <FiHash className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400 w-4 h-4" />
            <input type="text" value={hashInput} onChange={e => setHashInput(e.target.value)}
              placeholder="SHA-256 хеш документа..."
              className="w-full pl-11 pr-4 py-3.5 bg-slate-50 dark:bg-slate-900/50 rounded-xl text-sm font-mono
                border border-slate-200 dark:border-slate-600 focus:ring-2 focus:ring-blue-500 outline-none" />
          </div>
          <button
            onClick={() => { if (hashInput.length < 10) { toast.error('Введите хеш'); return; } verifyMutation.mutate(hashInput); }}
            disabled={verifyMutation.isPending}
            className="px-8 py-3.5 bg-gradient-to-r from-blue-600 to-blue-700 text-white rounded-xl font-semibold text-sm
              shadow-lg shadow-blue-500/25 hover:opacity-90 disabled:opacity-50 active:scale-95">
            {verifyMutation.isPending ? 'Поиск...' : 'Верифицировать'}
          </button>
        </div>
      </div>

      {/* ── Verify Result ── */}
      <AnimatePresence>
        {verifyResult && (
          <motion.div initial={{ opacity: 0, y: 24 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}
            className="bg-white dark:bg-slate-800 rounded-2xl shadow-sm border border-slate-200 dark:border-slate-700 overflow-hidden">
            <div className={`px-6 py-4 ${verifyResult.verified
              ? 'bg-gradient-to-r from-green-500 to-emerald-500'
              : 'bg-gradient-to-r from-red-500 to-rose-500'}`}>
              <div className="flex items-center gap-3">
                {verifyResult.verified
                  ? <FiCheckCircle className="w-7 h-7 text-white" />
                  : <FiXCircle className="w-7 h-7 text-white" />}
                <div>
                  <h3 className="text-lg font-bold text-white">
                    {verifyResult.verified ? 'Документ верифицирован' : 'Документ не найден'}
                  </h3>
                  <p className="text-sm text-white/80">
                    {verifyResult.verified ? 'Хеш подтверждён в цепочке' : 'Хеш отсутствует в блокчейне'}
                  </p>
                </div>
              </div>
            </div>
            {verifyResult.verified && (
              <div className="p-6 grid grid-cols-1 lg:grid-cols-[1fr_auto] gap-8">
                <div className="space-y-3">
                  <FactCard icon={FiLink}  label="ID закупки"       value={verifyResult.procurement_id || '—'} copyable />
                  <FactCard icon={FiClock} label="Время"            value={verifyResult.timestamp ? new Date(verifyResult.timestamp * 1000).toLocaleString('ru-RU') : '—'} />
                  <FactCard icon={FiHash}  label="Transaction Hash" value={verifyResult.tx_hash || '—'} mono copyable />
                  <FactCard icon={FiBox}   label="Block"            value={`#${verifyResult.block_number?.toLocaleString()}`} />
                </div>
                <div className="flex flex-col items-center justify-center p-6 bg-slate-50 dark:bg-slate-900/40 rounded-xl">
                  <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-4">QR верификации</p>
                  <div className="p-4 bg-white rounded-xl shadow-inner">
                    <QRCodeSVG value={`https://etherscan.io/tx/${verifyResult.tx_hash}`} size={140}
                      bgColor="#ffffff" fgColor="#0f172a" level="M" />
                  </div>
                  <a href={`https://etherscan.io/tx/${verifyResult.tx_hash}`} target="_blank" rel="noopener noreferrer"
                    className="mt-3 inline-flex items-center gap-1.5 text-xs text-blue-500 hover:text-blue-600 font-medium">
                    <FiExternalLink className="w-3 h-3" /> Открыть в Etherscan
                  </a>
                </div>
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>

      {/* ── Add Modal ── */}
      <AnimatePresence>
        {showAddModal && <AddContractModal onAdd={handleQueue} onClose={() => setShowAddModal(false)} />}
      </AnimatePresence>
    </div>
  );
}
