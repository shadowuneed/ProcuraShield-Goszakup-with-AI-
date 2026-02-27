'use client';

import { useQuery } from '@tanstack/react-query';
import { fetchAlerts } from '@/lib/api';
import { FiAlertTriangle, FiAlertCircle, FiInfo } from 'react-icons/fi';
import { clsx } from 'clsx';

const severityConfig: Record<string, { icon: typeof FiAlertTriangle; color: string; label: string }> = {
  critical: { icon: FiAlertTriangle, color: 'text-red-500 bg-red-50', label: 'Критический' },
  high: { icon: FiAlertCircle, color: 'text-orange-500 bg-orange-50', label: 'Высокий' },
  medium: { icon: FiInfo, color: 'text-yellow-500 bg-yellow-50', label: 'Средний' },
  low: { icon: FiInfo, color: 'text-blue-500 bg-blue-50', label: 'Низкий' },
};

export function RecentAlerts() {
  const { data } = useQuery({
    queryKey: ['recent-alerts'],
    queryFn: () => fetchAlerts({ limit: 5 }).then((r) => r.data),
  });

  // Демо-данные
  const alerts = data?.items || [
    { id: 1, title: 'Обнаружен сговор поставщиков', severity: 'critical', procurement_title: 'Строительство дороги', created_at: '2024-01-15T10:30:00' },
    { id: 2, title: 'Подозрительная спецификация', severity: 'high', procurement_title: 'Поставка медоборудования', created_at: '2024-01-15T09:15:00' },
    { id: 3, title: 'Аффилированные компании', severity: 'high', procurement_title: 'Ремонт школы', created_at: '2024-01-15T08:45:00' },
    { id: 4, title: 'Дробление платежей', severity: 'medium', procurement_title: 'Закупка ПО', created_at: '2024-01-14T16:20:00' },
    { id: 5, title: 'Нереалистичные сроки', severity: 'low', procurement_title: 'Благоустройство', created_at: '2024-01-14T14:10:00' },
  ];

  return (
    <div className="bg-white dark:bg-slate-800 rounded-xl p-5 shadow-sm border border-slate-200 dark:border-slate-700">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-100">
          Последние алерты
        </h3>
        <a
          href="/alerts"
          className="text-sm text-blue-600 hover:text-blue-700 font-medium"
        >
          Все алерты →
        </a>
      </div>
      <div className="space-y-3">
        {alerts.map((alert: Record<string, string | number>) => {
          const config = severityConfig[alert.severity as string] || severityConfig.low;
          const Icon = config.icon;
          return (
            <div
              key={alert.id}
              className="flex items-start gap-3 p-3 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors"
            >
              <div className={clsx('p-2 rounded-lg', config.color)}>
                <Icon className="w-4 h-4" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-slate-900 dark:text-slate-100">
                  {alert.title}
                </p>
                <p className="text-xs text-slate-500 mt-0.5">
                  {alert.procurement_title}
                </p>
              </div>
              <span className="text-xs text-slate-400 whitespace-nowrap">
                {new Date(alert.created_at as string).toLocaleTimeString('ru-RU', {
                  hour: '2-digit',
                  minute: '2-digit',
                })}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
