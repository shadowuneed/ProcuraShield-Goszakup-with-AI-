'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';
import {
  FiSettings, FiUser, FiBell, FiDatabase,
  FiSave, FiRefreshCw, FiKey, FiGlobe,
  FiMail, FiCpu, FiCheckCircle, FiSliders,
  FiToggleLeft, FiToggleRight,
} from 'react-icons/fi';
import toast from 'react-hot-toast';

const OLLAMA_URL = 'http://localhost:11434';
const AVAILABLE_MODELS = ['llama3:latest', 'deepseek-r1:8b'];

const TABS = [
  { key: 'general',  label: 'Общие',          icon: FiSettings },
  { key: 'profile',  label: 'Профиль',         icon: FiUser     },
  { key: 'notify',   label: 'Уведомления',     icon: FiBell     },
  { key: 'ai',       label: 'ИИ-настройки',    icon: FiCpu      },
  { key: 'data',     label: 'Данные и API',    icon: FiDatabase },
];

export default function SettingsPage() {
  const [tab, setTab] = useState('general');
  const [saving, setSaving] = useState(false);

  /* general */
  const [orgName, setOrgName]   = useState('ProcuraShield — Казахстан');
  const [chainId, setChainId]   = useState('1337');
  const [lang, setLang]         = useState('ru');
  const [theme, setTheme]       = useState('system');
  const [timezone, setTimezone] = useState('Asia/Almaty');

  /* profile */
  const [name, setName]   = useState('Администратор');
  const [email, setEmail] = useState('admin@procura.kz');
  const [role]            = useState('Суперадмин');

  /* notifications */
  const [notifs, setNotifs] = useState({
    newBlock:    true,
    fraudAlert:  true,
    aiReport:    true,
    systemError: true,
    weeklyReport:false,
    emailCopy:   false,
  });

  /* ai settings */
  const [autoAnalyze,   setAutoAnalyze]   = useState(true);
  const [analyzeOnMine, setAnalyzeOnMine] = useState(false);
  const [ollamaModel,   setOllamaModel]   = useState('llama3:latest');
  const [threshold,     setThreshold]     = useState(70);
  const [aiTestResult,  setAiTestResult]  = useState('');
  const [aiTesting,     setAiTesting]     = useState(false);

  /* data */
  const [backendUrl,  setBackendUrl]  = useState('http://localhost:8100');
  const [rpcUrl,      setRpcUrl]      = useState('http://localhost:8645');
  const [ipfsUrl,     setIpfsUrl]     = useState('http://localhost:5101');

  const save = () => {
    setSaving(true);
    setTimeout(() => { setSaving(false); toast.success('Настройки сохранены'); }, 900);
  };

  const testOllama = async () => {
    setAiTesting(true);
    setAiTestResult('');
    try {
      const res = await fetch('/api/ollama', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt: 'Ответь одним словом: работает', model: ollamaModel }),
      });
      const data = await res.json();
      if (data.error) { setAiTestResult(`✗ ${data.error}`); toast.error('Ошибка Ollama'); }
      else { setAiTestResult(`✓ Ollama (${data.model}) отвечает: «${String(data.text).trim().slice(0, 60)}»`); toast.success('Ollama работает!'); }
    } catch (e) { setAiTestResult(`✗ Нет связи с Ollama: ${String(e)}`); toast.error('Ollama недоступна'); }
    finally { setAiTesting(false); }
  };

  return (
    <div className="space-y-6 max-w-4xl mx-auto">

      {/* Header */}
      <div className="flex items-end justify-between">
        <div>
          <h1 className="text-3xl font-extrabold text-slate-900 dark:text-slate-100 tracking-tight">Настройки</h1>
          <p className="text-sm text-slate-500 mt-1">Конфигурация системы ProcuraShield</p>
        </div>
        <button onClick={save} disabled={saving}
          className="inline-flex items-center gap-2 px-4 py-2.5 bg-gradient-to-r from-blue-600 to-violet-600
                     text-white rounded-xl font-semibold text-sm shadow-lg shadow-blue-500/25 hover:opacity-90 active:scale-95 disabled:opacity-50">
          {saving ? <><FiRefreshCw className="w-4 h-4 animate-spin" /> Сохранение...</> : <><FiSave className="w-4 h-4" /> Сохранить</>}
        </button>
      </div>

      <div className="flex gap-6">
        {/* Sidebar tabs */}
        <nav className="flex flex-col gap-1 w-44 flex-shrink-0">
          {TABS.map(t => {
            const Icon = t.icon;
            return (
              <button key={t.key} onClick={() => setTab(t.key)}
                className={`flex items-center gap-2.5 px-3 py-2.5 rounded-xl text-sm font-medium transition-colors text-left ${
                  tab === t.key
                    ? 'bg-blue-600 text-white shadow-md shadow-blue-500/20'
                    : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-700/50'}`}>
                <Icon className="w-4 h-4 flex-shrink-0" /> {t.label}
              </button>
            );
          })}
        </nav>

        {/* Content */}
        <motion.div key={tab} initial={{ opacity: 0, x: 10 }} animate={{ opacity: 1, x: 0 }} transition={{ duration: 0.15 }}
          className="flex-1 rounded-2xl border border-slate-200 dark:border-slate-700/50 bg-white dark:bg-slate-800/40 p-6 space-y-5">

          {/* ── General ── */}
          {tab === 'general' && <>
            <h2 className="font-bold text-slate-800 dark:text-slate-100 text-base">Общие настройки</h2>
            {[
              { label: 'Название организации', value: orgName, set: setOrgName, type: 'text' },
              { label: 'Chain ID блокчейна',   value: chainId, set: setChainId, type: 'text' },
            ].map(f => (
              <div key={f.label}>
                <label className="block text-xs font-medium text-slate-500 mb-1.5">{f.label}</label>
                <input type={f.type} value={f.value} onChange={e => f.set(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900/50
                             text-sm text-slate-800 dark:text-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500/50" />
              </div>
            ))}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-medium text-slate-500 mb-1.5">Язык интерфейса</label>
                <select value={lang} onChange={e => setLang(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900/50
                             text-sm text-slate-800 dark:text-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500/50">
                  <option value="ru">Русский</option>
                  <option value="kk">Қазақша</option>
                  <option value="en">English</option>
                </select>
              </div>
              <div>
                <label className="block text-xs font-medium text-slate-500 mb-1.5">Тема оформления</label>
                <select value={theme} onChange={e => setTheme(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900/50
                             text-sm text-slate-800 dark:text-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500/50">
                  <option value="system">Системная</option>
                  <option value="light">Светлая</option>
                  <option value="dark">Тёмная</option>
                </select>
              </div>
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-500 mb-1.5">Часовой пояс</label>
              <select value={timezone} onChange={e => setTimezone(e.target.value)}
                className="w-full px-3 py-2 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900/50
                           text-sm text-slate-800 dark:text-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500/50">
                <option value="Asia/Almaty">Asia/Almaty (UTC+5)</option>
                <option value="Asia/Astana">Asia/Astana (UTC+5)</option>
                <option value="UTC">UTC</option>
              </select>
            </div>
          </>}

          {/* ── Profile ── */}
          {tab === 'profile' && <>
            <h2 className="font-bold text-slate-800 dark:text-slate-100 text-base">Профиль пользователя</h2>
            <div className="flex items-center gap-4 p-4 rounded-xl bg-slate-50 dark:bg-slate-900/40 border border-slate-200 dark:border-slate-700">
              <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-blue-500 to-violet-600 flex items-center justify-center text-white font-bold text-xl">
                {name[0]}
              </div>
              <div>
                <p className="font-bold text-slate-800 dark:text-slate-100">{name}</p>
                <p className="text-xs text-slate-500">{email}</p>
                <span className="inline-block mt-1 text-[10px] px-2 py-0.5 rounded-full bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 font-semibold">{role}</span>
              </div>
            </div>
            {[
              { label: 'Имя',            value: name,  set: setName,  icon: FiUser },
              { label: 'Email',          value: email, set: setEmail, icon: FiMail },
            ].map(f => (
              <div key={f.label}>
                <label className="block text-xs font-medium text-slate-500 mb-1.5">{f.label}</label>
                <div className="relative">
                  <f.icon className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-slate-400" />
                  <input value={f.value} onChange={e => f.set(e.target.value)}
                    className="w-full pl-8 pr-3 py-2 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900/50
                               text-sm text-slate-800 dark:text-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500/50" />
                </div>
              </div>
            ))}
          </>}

          {/* ── Notifications ── */}
          {tab === 'notify' && <>
            <h2 className="font-bold text-slate-800 dark:text-slate-100 text-base">Уведомления</h2>
            <div className="space-y-1">
              {[
                { key: 'newBlock',    label: 'Новый блок добавлен в цепочку',   desc: 'Push при каждом майнинге'           },
                { key: 'fraudAlert',  label: 'Обнаружено мошенничество',         desc: 'Высокоприоритетные алерты'          },
                { key: 'aiReport',    label: 'Готов ИИ-отчёт',                  desc: 'Ollama завершил анализ'             },
                { key: 'systemError', label: 'Системные ошибки',                 desc: 'Критические сбои и ошибки API'      },
                { key: 'weeklyReport',label: 'Еженедельный отчёт',              desc: 'Сводка по пятницам на email'        },
                { key: 'emailCopy',   label: 'Копия всех алертов на email',      desc: 'Дублирование push → email'          },
              ].map(n => (
                <div key={n.key} className="flex items-center justify-between py-3 border-b border-slate-100 dark:border-slate-700/50 last:border-0">
                  <div>
                    <p className="text-sm font-medium text-slate-800 dark:text-slate-100">{n.label}</p>
                    <p className="text-xs text-slate-500">{n.desc}</p>
                  </div>
                  <button onClick={() => setNotifs(p => ({ ...p, [n.key]: !p[n.key as keyof typeof p] }))}
                    className={`relative w-11 h-6 rounded-full transition-colors flex-shrink-0 ${notifs[n.key as keyof typeof notifs] ? 'bg-blue-500' : 'bg-slate-200 dark:bg-slate-600'}`}>
                    <span className={`absolute top-0.5 left-0.5 w-5 h-5 bg-white rounded-full shadow-sm transition-transform ${notifs[n.key as keyof typeof notifs] ? 'translate-x-5' : 'translate-x-0'}`} />
                  </button>
                </div>
              ))}
            </div>
          </>}

          {/* ── AI Settings ── */}
          {tab === 'ai' && <>
            <h2 className="font-bold text-slate-800 dark:text-slate-100 text-base">Настройки Ollama (локальный ИИ)</h2>

            {/* Ollama status */}
            <div className="rounded-xl bg-slate-50 dark:bg-slate-900/40 border border-slate-200 dark:border-slate-700 p-4">
              <div className="flex items-center justify-between mb-3">
                <div>
                  <p className="text-sm font-semibold text-slate-700 dark:text-slate-200">Ollama сервер</p>
                  <p className="text-xs text-slate-400 font-mono">{OLLAMA_URL}</p>
                </div>
                <button onClick={testOllama} disabled={aiTesting}
                  className="px-4 py-2 rounded-xl bg-fuchsia-600 text-white text-sm font-semibold hover:bg-fuchsia-700 disabled:opacity-50
                             inline-flex items-center gap-1.5">
                  {aiTesting ? <FiRefreshCw className="w-3.5 h-3.5 animate-spin" /> : <FiCpu className="w-3.5 h-3.5" />}
                  Проверить
                </button>
              </div>
              {aiTestResult && (
                <p className={`text-xs font-medium ${aiTestResult.startsWith('✓') ? 'text-emerald-500' : 'text-red-500'}`}>
                  {aiTestResult}
                </p>
              )}
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-500 mb-1.5">Модель для анализа</label>
              <div className="flex flex-wrap gap-2">
                {AVAILABLE_MODELS.map(m => (
                  <button key={m} onClick={() => setOllamaModel(m)}
                    className={`px-3 py-1.5 rounded-lg text-xs font-mono font-semibold border transition-colors ${
                      ollamaModel === m
                        ? 'bg-fuchsia-600 border-fuchsia-600 text-white'
                        : 'bg-slate-100 dark:bg-slate-800 border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-300 hover:border-fuchsia-500'}`}>
                    {m}
                  </button>
                ))}
              </div>
              <p className="text-xs text-slate-400 mt-1">Выбрано: <span className="font-mono text-fuchsia-400">{ollamaModel}</span></p>
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-500 mb-1.5">
                Порог риска для авто-алерта: <span className="text-blue-500 font-bold">{threshold}%</span>
              </label>
              <input type="range" min={10} max={95} value={threshold} onChange={e => setThreshold(+e.target.value)}
                className="w-full accent-blue-600" />
              <div className="flex justify-between text-[10px] text-slate-400 mt-1">
                <span>10% (много алертов)</span><span>95% (только критичное)</span>
              </div>
            </div>

            <div className="space-y-3 pt-2">
              {[
                { label: 'Авто-анализ при открытии блокчейна', value: autoAnalyze,   set: setAutoAnalyze   },
                { label: 'Анализировать при каждом майнинге',  value: analyzeOnMine, set: setAnalyzeOnMine },
              ].map(s => (
                <div key={s.label} className="flex items-center justify-between py-2 border-b border-slate-100 dark:border-slate-700/50 last:border-0">
                  <p className="text-sm text-slate-700 dark:text-slate-300">{s.label}</p>
                  <button onClick={() => s.set((v: boolean) => !v)}
                    className={`relative w-11 h-6 rounded-full transition-colors ${s.value ? 'bg-fuchsia-500' : 'bg-slate-200 dark:bg-slate-600'}`}>
                    <span className={`absolute top-0.5 left-0.5 w-5 h-5 bg-white rounded-full shadow-sm transition-transform ${s.value ? 'translate-x-5' : 'translate-x-0'}`} />
                  </button>
                </div>
              ))}
            </div>

            {/* AI Capabilities info */}
            <div className="rounded-xl bg-gradient-to-br from-violet-950/40 to-fuchsia-950/30 border border-violet-700/30 p-4">
              <p className="text-xs font-bold text-violet-300 uppercase tracking-wider mb-3">Возможности локального ИИ (Ollama) в ProcuraShield</p>
              <ul className="space-y-2">
                {[
                  '🔍 Обнаружение дубликатов контрактов (один поставщик, одинаковые суммы)',
                  '📊 Анализ паттернов мошенничества (дробление сумм, завышение цен)',
                  '🛡️ Анализ угроз безопасности и подозрительных IP в реальном времени',
                  '🔗 Проверка связей между поставщиками (аффилированность)',
                  '📄 Обработка документов закупок (PDF/Excel) и выявление рисков',
                  '📈 Прогнозирование риска будущих закупок на основе истории',
                  '💬 Объяснение любого нарушения на естественном языке',
                ].map((item, i) => (
                  <li key={i} className="text-xs text-slate-300 flex items-start gap-2">
                    <FiCheckCircle className="w-3 h-3 text-fuchsia-400 mt-0.5 flex-shrink-0" />
                    {item}
                  </li>
                ))}
              </ul>
            </div>
          </>}

          {/* ── Data & API ── */}
          {tab === 'data' && <>
            <h2 className="font-bold text-slate-800 dark:text-slate-100 text-base">Данные и API-подключения</h2>
            {[
              { label: 'Backend API URL',  value: backendUrl,  set: setBackendUrl,  icon: FiGlobe    },
              { label: 'Ethereum RPC URL', value: rpcUrl,      set: setRpcUrl,      icon: FiDatabase },
              { label: 'IPFS Node URL',    value: ipfsUrl,     set: setIpfsUrl,     icon: FiDatabase },
            ].map(f => (
              <div key={f.label}>
                <label className="block text-xs font-medium text-slate-500 mb-1.5">{f.label}</label>
                <div className="relative">
                  <f.icon className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-slate-400" />
                  <input value={f.value} onChange={e => f.set(e.target.value)}
                    className="w-full pl-8 pr-3 py-2 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900/50
                               text-sm font-mono text-slate-800 dark:text-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500/50" />
                </div>
              </div>
            ))}
            <div className="rounded-xl bg-amber-50 dark:bg-amber-950/20 border border-amber-200 dark:border-amber-800/30 p-4">
              <p className="text-xs text-amber-700 dark:text-amber-400 font-medium">
                ⚠ Изменение URL-адресов требует перезапуска сервисов. Убедитесь, что указанные адреса доступны.
              </p>
            </div>
          </>}

        </motion.div>
      </div>
    </div>
  );
}
