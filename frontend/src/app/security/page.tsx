'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  FiShield, FiAlertTriangle, FiCheckCircle, FiXCircle,
  FiCpu, FiLock, FiUnlock, FiEye, FiEyeOff,
  FiRefreshCw, FiX, FiActivity, FiUser, FiClock,
  FiAlertOctagon, FiWifi, FiKey, FiTrendingUp,
} from 'react-icons/fi';
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

/* ────────── mock data ────────── */
const ACCESS_LOGS = [
  { id: 1, user: 'admin@procura.kz',    action: 'Вход в систему',            ip: '192.168.1.5',  time: '25.02.2026 15:42', status: 'success' },
  { id: 2, user: 'auditor@gov.kz',      action: 'Просмотр блокчейна',         ip: '10.0.0.14',    time: '25.02.2026 15:38', status: 'success' },
  { id: 3, user: 'unknown@ext.ru',      action: 'Попытка входа (неверный пароль)', ip: '91.234.12.7', time: '25.02.2026 15:30', status: 'failed' },
  { id: 4, user: 'manager@akimat.kz',   action: 'Экспорт данных',             ip: '172.16.0.8',   time: '25.02.2026 14:55', status: 'success' },
  { id: 5, user: 'unknown@ext.ru',      action: 'Попытка API (/admin/users)', ip: '91.234.12.7',  time: '25.02.2026 14:44', status: 'blocked' },
  { id: 6, user: 'analyst@procura.kz',  action: 'Запуск ИИ-анализа',         ip: '192.168.1.9',  time: '25.02.2026 14:20', status: 'success' },
  { id: 7, user: 'bot?',                action: 'Сканирование портов 80/443', ip: '185.220.101.3',time: '25.02.2026 13:11', status: 'blocked' },
];

const THREATS = [
  { id: 1, title: 'Брутфорс-атака',        desc: 'IP 91.234.12.7 — 14 неудачных попыток за 5 мин', severity: 'high',   active: true  },
  { id: 2, title: 'Сканирование портов',    desc: 'IP 185.220.101.3 — попытка сканирования',         severity: 'medium', active: true  },
  { id: 3, title: 'Подозрительный экспорт', desc: 'manager@akimat.kz — нетипичное время активности', severity: 'low',    active: true  },
  { id: 4, title: 'DDOS-попытка',           desc: 'Заблокировано на уровне файервола',                severity: 'high',   active: false },
];

const MODULES = [
  { key: 'mfa',         label: 'Двухфакторная аутентификация', desc: 'TOTP/SMS для всех пользователей',  enabled: true  },
  { key: 'rateLimit',   label: 'Rate Limiting',                 desc: 'Лимит 100 запросов/мин на IP',     enabled: true  },
  { key: 'encryptLogs', label: 'Шифрование логов',              desc: 'AES-256 для архивов аудита',       enabled: true  },
  { key: 'ipWhitelist', label: 'IP-белый список',               desc: 'Доступ только с доверенных IP',    enabled: false },
  { key: 'apiSigning',  label: 'Подпись API-запросов',          desc: 'HMAC-SHA256 для всех запросов',    enabled: false },
  { key: 'autoBlock',   label: 'Авто-блокировка',               desc: 'Блок IP после 5 неудачных входов', enabled: true  },
];

interface AiThreatResult {
  summary: string;
  overallLevel: 'critical' | 'high' | 'medium' | 'low';
  threatAnalysis: { threat: string; explanation: string; recommendation: string; severity: 'critical' | 'high' | 'medium' | 'low' }[];
  suspiciousIps: { ip: string; reason: string }[];
  immediateActions: string[];
}

export default function SecurityPage() {
  const [modules, setModules] = useState(MODULES);
  const [aiLoading, setAiLoading] = useState(false);
  const [aiResult, setAiResult] = useState<AiThreatResult | null>(null);
  const [showAi, setShowAi] = useState(false);
  const [showAllLogs, setShowAllLogs] = useState(false);

  const toggleModule = (key: string) => {
    setModules(prev => prev.map(m => m.key === key ? { ...m, enabled: !m.enabled } : m));
    const m = modules.find(m => m.key === key);
    toast.success(`${m?.label} ${m?.enabled ? 'отключён' : 'включён'}`);
  };

  const analyzeThreats = async () => {
    setAiLoading(true);
    setShowAi(true);
    setAiResult(null);
    try {
      const prompt = `Ты эксперт по кибербезопасности системы государственных закупок ProcuraShield.
Проанализируй следующие угрозы и логи доступа на предмет реальных атак и уязвимостей.

Активные угрозы:
${JSON.stringify(THREATS.filter(t => t.active), null, 2)}

Логи доступа (последние события):
${JSON.stringify(ACCESS_LOGS, null, 2)}

Задание:
1. Оцени каждую угрозу: реальная ли это атака или ложная тревога
2. Выяви подозрительные IP и пользователей
3. Дай конкретные рекомендации по защите

Ответь СТРОГО в JSON без лишнего текста:
{
  "summary": "краткий вывод на русском",
  "overallLevel": "critical|high|medium|low",
  "threatAnalysis": [{"threat": "название", "explanation": "объяснение", "recommendation": "действие", "severity": "critical|high|medium|low"}],
  "suspiciousIps": [{"ip": "адрес", "reason": "причина"}],
  "immediateActions": ["действие 1", "действие 2"]
}`;
      const raw = await callOllama(prompt);
      const match = raw.match(/\{[\s\S]*\}/);
      if (match) setAiResult(JSON.parse(match[0]));
      else toast.error('ИИ не вернул корректный JSON. Попробуйте снова.');
    } catch (e) { toast.error(`Ошибка Ollama: ${String(e)}`); }
    finally { setAiLoading(false); }
  };

  const sevColor = (s: string) =>
    s === 'critical' ? 'text-red-400 bg-red-950/40 border-red-800/50' :
    s === 'high'     ? 'text-orange-400 bg-orange-950/40 border-orange-800/50' :
    s === 'medium'   ? 'text-yellow-400 bg-yellow-950/40 border-yellow-800/50' :
                       'text-emerald-400 bg-emerald-950/40 border-emerald-800/50';

  const displayedLogs = showAllLogs ? ACCESS_LOGS : ACCESS_LOGS.slice(0, 4);

  return (
    <div className="space-y-8 max-w-7xl mx-auto">

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4">
        <div>
          <h1 className="text-3xl font-extrabold text-slate-900 dark:text-slate-100 tracking-tight">
            Безопасность
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Мониторинг угроз · Журнал доступа · Защитные модули
          </p>
        </div>
        <button onClick={analyzeThreats} disabled={aiLoading}
          className="inline-flex items-center gap-2 px-4 py-2.5 bg-gradient-to-r from-violet-600 to-fuchsia-600
                     text-white rounded-xl font-semibold text-sm shadow-lg shadow-violet-500/25 hover:opacity-90 active:scale-95 disabled:opacity-40">
          {aiLoading
            ? <><FiRefreshCw className="w-4 h-4 animate-spin" /> Анализирую...</>
            : <><FiCpu className="w-4 h-4" /> ИИ-анализ угроз</>}
        </button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        {[
          { label: 'Активных угроз',      value: THREATS.filter(t => t.active).length,                icon: FiAlertOctagon, color: 'text-red-500',     bg: 'bg-red-50 dark:bg-red-900/20',      border: 'border-red-100 dark:border-red-900/40'      },
          { label: 'Заблокировано IP',     value: ACCESS_LOGS.filter(l => l.status === 'blocked').length, icon: FiLock,      color: 'text-orange-500',  bg: 'bg-orange-50 dark:bg-orange-900/20',border: 'border-orange-100 dark:border-orange-900/40' },
          { label: 'Успешных входов',      value: ACCESS_LOGS.filter(l => l.status === 'success').length, icon: FiCheckCircle, color: 'text-emerald-500',bg: 'bg-emerald-50 dark:bg-emerald-900/20',border: 'border-emerald-100 dark:border-emerald-900/40'},
          { label: 'Модулей защиты',       value: `${modules.filter(m => m.enabled).length}/${modules.length}`, icon: FiShield, color: 'text-blue-500', bg: 'bg-blue-50 dark:bg-blue-900/20',    border: 'border-blue-100 dark:border-blue-900/40'    },
        ].map((s, i) => {
          const Icon = s.icon;
          return (
            <motion.div key={i} initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.06 }}
              className={`rounded-2xl border p-5 ${s.bg} ${s.border}`}>
              <div className="flex items-center justify-between mb-2">
                <p className="text-xs font-medium text-slate-500 dark:text-slate-400">{s.label}</p>
                <Icon className={`w-4 h-4 ${s.color}`} />
              </div>
              <p className={`text-2xl font-extrabold ${s.color}`}>{s.value}</p>
            </motion.div>
          );
        })}
      </div>

      {/* AI Panel */}
      <AnimatePresence>
        {showAi && (
          <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: 16 }}
            className="rounded-2xl border border-violet-700/40 bg-gradient-to-br from-[#120d1f] via-[#170d2a] to-[#0d1117] shadow-2xl overflow-hidden">
            <div className="flex items-center justify-between px-6 py-4 border-b border-violet-800/40">
              <div className="flex items-center gap-3">
                <FiCpu className="w-5 h-5 text-fuchsia-400" />
                <span className="font-bold text-slate-100">Ollama ИИ — Анализ угроз безопасности</span>
                {aiResult && (
                  <span className={`text-xs px-2 py-0.5 rounded-full font-semibold border ${sevColor(aiResult.overallLevel)}`}>
                    {aiResult.overallLevel === 'critical' ? '🔴 Критический' :
                     aiResult.overallLevel === 'high'     ? '🟠 Высокий' :
                     aiResult.overallLevel === 'medium'   ? '🟡 Средний' : '🟢 Низкий'}
                  </span>
                )}
              </div>
              <button onClick={() => setShowAi(false)}
                className="w-7 h-7 flex items-center justify-center rounded-lg text-slate-400 hover:text-white hover:bg-slate-700/50">
                <FiX className="w-4 h-4" />
              </button>
            </div>

            {aiLoading && (
              <div className="flex flex-col items-center justify-center py-12 gap-4">
                <FiCpu className="w-10 h-10 text-fuchsia-400 animate-pulse" />
                <p className="text-slate-400 text-sm">Ollama ({OLLAMA_MODEL}) анализирует угрозы и логи доступа...</p>
              </div>
            )}

            {!aiLoading && aiResult && (
              <div className="p-6 space-y-6">
                <p className="text-slate-300 text-sm leading-relaxed">{aiResult.summary}</p>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3 flex items-center gap-2">
                      <FiAlertTriangle className="w-3.5 h-3.5" /> Анализ угроз
                    </h3>
                    <div className="space-y-2">
                      {aiResult.threatAnalysis.map((t, i) => (
                        <div key={i} className={`rounded-xl p-3 border ${sevColor(t.severity)}`}>
                          <p className="text-xs font-bold mb-1">{t.threat}</p>
                          <p className="text-xs opacity-80 mb-1">{t.explanation}</p>
                          <p className="text-xs font-medium">→ {t.recommendation}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                  <div className="space-y-6">
                    <div>
                      <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3 flex items-center gap-2">
                        <FiWifi className="w-3.5 h-3.5" /> Подозрительные IP
                      </h3>
                      {aiResult.suspiciousIps.length === 0
                        ? <p className="text-xs text-emerald-400">✓ Подозрительных IP не обнаружено</p>
                        : <div className="space-y-2">{aiResult.suspiciousIps.map((ip, i) => (
                            <div key={i} className="rounded-xl p-3 bg-red-950/30 border border-red-800/40">
                              <p className="text-xs font-mono font-bold text-red-300">{ip.ip}</p>
                              <p className="text-xs text-slate-400 mt-0.5">{ip.reason}</p>
                            </div>
                          ))}</div>}
                    </div>
                    <div>
                      <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3 flex items-center gap-2">
                        <FiShield className="w-3.5 h-3.5" /> Немедленные действия
                      </h3>
                      <ul className="space-y-1.5">
                        {aiResult.immediateActions.map((a, i) => (
                          <li key={i} className="flex items-start gap-2 text-xs text-slate-300">
                            <span className="text-fuchsia-400 mt-0.5 flex-shrink-0">→</span> {a}
                          </li>
                        ))}
                      </ul>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Active Threats */}
        <div className="rounded-2xl border border-slate-200 dark:border-slate-700/50 bg-white dark:bg-slate-800/40 p-6">
          <h2 className="flex items-center gap-2 font-bold text-slate-800 dark:text-slate-100 mb-4">
            <FiAlertOctagon className="w-4 h-4 text-red-500" /> Активные угрозы
          </h2>
          <div className="space-y-3">
            {THREATS.map(t => (
              <div key={t.id} className={`flex items-start gap-3 p-3 rounded-xl border ${
                !t.active ? 'opacity-40' :
                t.severity === 'high'   ? 'bg-red-50 dark:bg-red-950/30 border-red-200 dark:border-red-800/40' :
                t.severity === 'medium' ? 'bg-orange-50 dark:bg-orange-950/30 border-orange-200 dark:border-orange-800/40' :
                                          'bg-yellow-50 dark:bg-yellow-950/30 border-yellow-200 dark:border-yellow-800/40'}`}>
                {t.active
                  ? <FiAlertTriangle className={`w-4 h-4 mt-0.5 flex-shrink-0 ${t.severity === 'high' ? 'text-red-500' : t.severity === 'medium' ? 'text-orange-500' : 'text-yellow-500'}`} />
                  : <FiCheckCircle className="w-4 h-4 mt-0.5 flex-shrink-0 text-slate-400" />}
                <div>
                  <p className="text-sm font-semibold text-slate-800 dark:text-slate-100">{t.title}</p>
                  <p className="text-xs text-slate-500 mt-0.5">{t.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Protection Modules */}
        <div className="rounded-2xl border border-slate-200 dark:border-slate-700/50 bg-white dark:bg-slate-800/40 p-6">
          <h2 className="flex items-center gap-2 font-bold text-slate-800 dark:text-slate-100 mb-4">
            <FiShield className="w-4 h-4 text-blue-500" /> Модули защиты
          </h2>
          <div className="space-y-3">
            {modules.map(m => (
              <div key={m.key} className="flex items-center justify-between py-2">
                <div className="flex items-center gap-3">
                  {m.enabled
                    ? <FiLock className="w-4 h-4 text-emerald-500 flex-shrink-0" />
                    : <FiUnlock className="w-4 h-4 text-slate-400 flex-shrink-0" />}
                  <div>
                    <p className="text-sm font-medium text-slate-800 dark:text-slate-100">{m.label}</p>
                    <p className="text-xs text-slate-500">{m.desc}</p>
                  </div>
                </div>
                <button onClick={() => toggleModule(m.key)}
                  className={`relative w-11 h-6 rounded-full transition-colors flex-shrink-0 ${m.enabled ? 'bg-emerald-500' : 'bg-slate-300 dark:bg-slate-600'}`}>
                  <span className={`absolute top-0.5 left-0.5 w-5 h-5 bg-white rounded-full shadow-sm transition-transform ${m.enabled ? 'translate-x-5' : 'translate-x-0'}`} />
                </button>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Access Log */}
      <div className="rounded-2xl border border-slate-200 dark:border-slate-700/50 bg-white dark:bg-slate-800/40 p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="flex items-center gap-2 font-bold text-slate-800 dark:text-slate-100">
            <FiActivity className="w-4 h-4 text-violet-500" /> Журнал доступа
          </h2>
          <button onClick={() => setShowAllLogs(v => !v)}
            className="text-xs text-violet-500 hover:underline">{showAllLogs ? 'Скрыть' : 'Показать всё'}</button>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr className="border-b border-slate-200 dark:border-slate-700">
                {['Пользователь','Действие','IP-адрес','Время','Статус'].map(h => (
                  <th key={h} className="text-left text-slate-400 font-medium pb-2 pr-4">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
              {displayedLogs.map(log => (
                <tr key={log.id} className="hover:bg-slate-50 dark:hover:bg-slate-700/20 transition-colors">
                  <td className="py-2.5 pr-4">
                    <div className="flex items-center gap-1.5">
                      <FiUser className="w-3 h-3 text-slate-400" />
                      <span className="font-mono text-slate-700 dark:text-slate-300">{log.user}</span>
                    </div>
                  </td>
                  <td className="py-2.5 pr-4 text-slate-600 dark:text-slate-400">{log.action}</td>
                  <td className="py-2.5 pr-4 font-mono text-slate-500">{log.ip}</td>
                  <td className="py-2.5 pr-4">
                    <div className="flex items-center gap-1 text-slate-500">
                      <FiClock className="w-3 h-3" /> {log.time}
                    </div>
                  </td>
                  <td className="py-2.5">
                    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full font-semibold text-[10px] ${
                      log.status === 'success' ? 'bg-emerald-100 dark:bg-emerald-900/30 text-emerald-600 dark:text-emerald-400' :
                      log.status === 'failed'  ? 'bg-orange-100 dark:bg-orange-900/30 text-orange-600 dark:text-orange-400' :
                                                 'bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-400'}`}>
                      {log.status === 'success' && <FiCheckCircle className="w-2.5 h-2.5" />}
                      {log.status === 'failed'  && <FiAlertTriangle className="w-2.5 h-2.5" />}
                      {log.status === 'blocked' && <FiXCircle className="w-2.5 h-2.5" />}
                      {log.status === 'success' ? 'Успех' : log.status === 'failed' ? 'Ошибка' : 'Заблокирован'}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

    </div>
  );
}
