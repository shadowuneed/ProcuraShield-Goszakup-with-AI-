'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { fetchProcurements, searchProcurements } from '@/lib/api';
import { FiSearch, FiFilter, FiExternalLink, FiActivity } from 'react-icons/fi';
import { clsx } from 'clsx';
import Link from 'next/link';

interface Procurement {
  id: number;
  number: string;
  title: string;
  organization: string;
  amount: number;
  status: string;
  risk_score?: number;
  risk_level?: string;
  published_at: string;
}

const demoProcurements: Procurement[] = [
  { id: 1, number: 'ГЗ-2024-001234', title: 'Строительство автомобильной дороги Астана-Щучинск, участок 45-67 км', organization: 'АО "КазАвтоЖол"', amount: 2_450_000_000, status: 'active', risk_score: 92, risk_level: 'red', published_at: '2024-01-10' },
  { id: 2, number: 'ГЗ-2024-001235', title: 'Поставка медицинского оборудования для городских поликлиник', organization: 'УОЗ г.Алматы', amount: 890_000_000, status: 'active', risk_score: 87, risk_level: 'red', published_at: '2024-01-11' },
  { id: 3, number: 'ГЗ-2024-001236', title: 'Капитальный ремонт средней школы №45', organization: 'Акимат Караганды', amount: 345_000_000, status: 'completed', risk_score: 78, risk_level: 'orange', published_at: '2024-01-12' },
  { id: 4, number: 'ГЗ-2024-001237', title: 'Закупка программного обеспечения для ГИС', organization: 'МЦР РК', amount: 567_000_000, status: 'active', risk_score: 74, risk_level: 'orange', published_at: '2024-01-13' },
  { id: 5, number: 'ГЗ-2024-001238', title: 'Благоустройство центрального парка', organization: 'Акимат Шымкента', amount: 234_000_000, status: 'active', risk_score: 45, risk_level: 'yellow', published_at: '2024-01-14' },
  { id: 6, number: 'ГЗ-2024-001239', title: 'Поставка канцелярских товаров', organization: 'МОН РК', amount: 15_000_000, status: 'completed', risk_score: 12, risk_level: 'green', published_at: '2024-01-15' },
];

export default function ProcurementsPage() {
  const [search, setSearch] = useState('');
  const [riskFilter, setRiskFilter] = useState<string>('all');

  const { data } = useQuery({
    queryKey: ['procurements', search],
    queryFn: () =>
      search
        ? searchProcurements(search).then((r) => r.data)
        : fetchProcurements().then((r) => r.data),
  });

  const procurements: Procurement[] = data?.items || demoProcurements;

  const filtered = riskFilter === 'all'
    ? procurements
    : procurements.filter((p) => p.risk_level === riskFilter);

  const formatAmount = (amount: number) =>
    new Intl.NumberFormat('ru-RU', { style: 'currency', currency: 'KZT', maximumFractionDigits: 0 })
      .format(amount);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">
          Закупки
        </h1>
        <p className="text-sm text-slate-500 mt-1">
          Реестр государственных закупок с AI-анализом рисков
        </p>
      </div>

      {/* Поиск и фильтры */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="flex-1 relative">
          <FiSearch className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 w-4 h-4" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Поиск по номеру, названию, организации..."
            className="w-full pl-10 pr-4 py-2.5 bg-white dark:bg-slate-800 rounded-lg text-sm
                       border border-slate-200 dark:border-slate-700 focus:ring-2 focus:ring-blue-500 outline-none"
          />
        </div>
        <div className="flex items-center gap-2">
          <FiFilter className="w-4 h-4 text-slate-400" />
          {['all', 'red', 'orange', 'yellow', 'green'].map((f) => (
            <button
              key={f}
              onClick={() => setRiskFilter(f)}
              className={clsx(
                'px-3 py-2 rounded-lg text-xs font-medium transition-colors',
                riskFilter === f
                  ? 'bg-blue-600 text-white'
                  : 'bg-slate-100 dark:bg-slate-800 text-slate-600 hover:bg-slate-200'
              )}
            >
              {f === 'all' ? 'Все' : f === 'red' ? 'Высокий' : f === 'orange' ? 'Повышенный' : f === 'yellow' ? 'Средний' : 'Низкий'}
            </button>
          ))}
        </div>
      </div>

      {/* Таблица */}
      <div className="bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-slate-200 dark:border-slate-700 overflow-hidden">
        <table className="w-full">
          <thead className="bg-slate-50 dark:bg-slate-900/50">
            <tr>
              <th className="text-left text-xs font-medium text-slate-500 uppercase px-4 py-3">Номер</th>
              <th className="text-left text-xs font-medium text-slate-500 uppercase px-4 py-3">Название</th>
              <th className="text-left text-xs font-medium text-slate-500 uppercase px-4 py-3">Заказчик</th>
              <th className="text-right text-xs font-medium text-slate-500 uppercase px-4 py-3">Сумма</th>
              <th className="text-center text-xs font-medium text-slate-500 uppercase px-4 py-3">Риск</th>
              <th className="text-center text-xs font-medium text-slate-500 uppercase px-4 py-3">Действия</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 dark:divide-slate-700">
            {filtered.map((proc) => (
              <tr key={proc.id} className="hover:bg-slate-50 dark:hover:bg-slate-700/30 transition-colors">
                <td className="px-4 py-3">
                  <span className="text-sm font-mono text-slate-600 dark:text-slate-400">
                    {proc.number}
                  </span>
                </td>
                <td className="px-4 py-3">
                  <p className="text-sm font-medium text-slate-900 dark:text-slate-100 max-w-xs truncate">
                    {proc.title}
                  </p>
                  <p className="text-xs text-slate-400">{proc.published_at}</p>
                </td>
                <td className="px-4 py-3">
                  <span className="text-sm text-slate-600 dark:text-slate-400">
                    {proc.organization}
                  </span>
                </td>
                <td className="px-4 py-3 text-right">
                  <span className="text-sm font-medium text-slate-900 dark:text-slate-100">
                    {formatAmount(proc.amount)}
                  </span>
                </td>
                <td className="px-4 py-3 text-center">
                  {proc.risk_score !== undefined && (
                    <span
                      className={clsx(
                        'inline-flex items-center px-2.5 py-1 rounded-full text-xs font-bold',
                        proc.risk_level === 'red' && 'bg-red-100 text-red-700',
                        proc.risk_level === 'orange' && 'bg-orange-100 text-orange-700',
                        proc.risk_level === 'yellow' && 'bg-yellow-100 text-yellow-700',
                        proc.risk_level === 'green' && 'bg-green-100 text-green-700'
                      )}
                    >
                      {proc.risk_score}%
                    </span>
                  )}
                </td>
                <td className="px-4 py-3 text-center">
                  <div className="flex items-center justify-center gap-2">
                    <Link
                      href={`/analysis?id=${proc.id}`}
                      className="p-1.5 text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                      title="Анализировать"
                    >
                      <FiActivity className="w-4 h-4" />
                    </Link>
                    <button
                      className="p-1.5 text-slate-400 hover:bg-slate-100 rounded-lg transition-colors"
                      title="Подробнее"
                    >
                      <FiExternalLink className="w-4 h-4" />
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
