'use client';

import {
  FiTrendingUp,
  FiAlertTriangle,
  FiCheckCircle,
  FiClock,
} from 'react-icons/fi';

interface StatsCardsProps {
  stats?: {
    total_procurements: number;
    today_count: number;
    high_risk_count: number;
    analyzed_count: number;
  };
}

const cards = [
  {
    key: 'total_procurements',
    label: 'Всего закупок',
    icon: FiTrendingUp,
    color: 'text-blue-600 bg-blue-100',
    format: (v: number) => v?.toLocaleString('ru-RU') || '0',
  },
  {
    key: 'today_count',
    label: 'Сегодня',
    icon: FiClock,
    color: 'text-emerald-600 bg-emerald-100',
    format: (v: number) => v?.toString() || '0',
  },
  {
    key: 'high_risk_count',
    label: 'Высокий риск',
    icon: FiAlertTriangle,
    color: 'text-red-600 bg-red-100',
    format: (v: number) => v?.toString() || '0',
  },
  {
    key: 'analyzed_count',
    label: 'Проанализировано',
    icon: FiCheckCircle,
    color: 'text-purple-600 bg-purple-100',
    format: (v: number) => v?.toLocaleString('ru-RU') || '0',
  },
];

export function StatsCards({ stats }: StatsCardsProps) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {cards.map((card) => (
        <div
          key={card.key}
          className="bg-white dark:bg-slate-800 rounded-xl p-5 shadow-sm
                     border border-slate-200 dark:border-slate-700
                     hover:shadow-md transition-shadow"
        >
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-slate-500 dark:text-slate-400">
                {card.label}
              </p>
              <p className="text-2xl font-bold text-slate-900 dark:text-slate-100 mt-1">
                {card.format((stats as Record<string, number>)?.[card.key])}
              </p>
            </div>
            <div className={`p-3 rounded-lg ${card.color}`}>
              <card.icon className="w-6 h-6" />
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
