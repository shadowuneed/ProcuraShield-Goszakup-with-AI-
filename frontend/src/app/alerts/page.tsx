'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { fetchAlerts, api } from '@/lib/api';
import { clsx } from 'clsx';
import { FiAlertTriangle, FiAlertCircle, FiInfo, FiCheck, FiFilter } from 'react-icons/fi';

interface Alert {
  id: number;
  title: string;
  description: string;
  severity: string;
  procurement_title: string;
  status: string;
  created_at: string;
}

export default function AlertsPage() {
  const [filter, setFilter] = useState<string>('all');
  const queryClient = useQueryClient();

  const { data, isLoading } = useQuery({
    queryKey: ['alerts', filter],
    queryFn: () =>
      fetchAlerts({ severity: filter !== 'all' ? filter : undefined }).then(
        (r) => r.data
      ),
  });

  const resolveMutation = useMutation({
    mutationFn: (id: number) =>
      api.put(`/api/alerts/${id}`, { status: 'resolved' }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['alerts'] });
    },
  });

  // Демо-данные алертов
  const alerts: Alert[] = data?.items || [
    { id: 1, title: 'Обнаружен картельный сговор', description: 'Три компании подали одинаковые заявки с ценами в пределах 1%', severity: 'critical', procurement_title: 'Строительство дороги Астана-Щучинск', status: 'new', created_at: '2024-01-15T10:30:00' },
    { id: 2, title: 'Гиперспецифичная спецификация', description: 'Указан конкретный бренд без допуска аналогов', severity: 'high', procurement_title: 'Поставка серверного оборудования', status: 'new', created_at: '2024-01-15T09:15:00' },
    { id: 3, title: 'Аффилированные участники', description: 'Директора двух компаний-участников имеют общий адрес регистрации', severity: 'high', procurement_title: 'Ремонт школы №45', status: 'reviewing', created_at: '2024-01-15T08:45:00' },
    { id: 4, title: 'Подозрение на дробление платежей', description: '7 платежей за 24 часа на общую сумму 15 млн тг', severity: 'medium', procurement_title: 'Закупка канцелярии', status: 'new', created_at: '2024-01-14T16:20:00' },
    { id: 5, title: 'Нереалистичные сроки исполнения', description: 'Требуемый срок 10 дней при среднем по отрасли 90 дней', severity: 'medium', procurement_title: 'Внедрение ИС', status: 'resolved', created_at: '2024-01-14T14:10:00' },
    { id: 6, title: 'Компания-однодневка', description: 'Победитель зарегистрирован 2 месяца назад, уставный капитал минимальный', severity: 'high', procurement_title: 'Поставка медикаментов', status: 'new', created_at: '2024-01-14T11:05:00' },
  ];

  const filteredAlerts = filter === 'all'
    ? alerts
    : alerts.filter((a) => a.severity === filter);

  const severityConfig: Record<string, { icon: typeof FiAlertTriangle; color: string; label: string }> = {
    critical: { icon: FiAlertTriangle, color: 'border-l-red-600 bg-red-50 dark:bg-red-900/10', label: 'Критический' },
    high: { icon: FiAlertCircle, color: 'border-l-orange-500 bg-orange-50 dark:bg-orange-900/10', label: 'Высокий' },
    medium: { icon: FiInfo, color: 'border-l-yellow-500 bg-yellow-50 dark:bg-yellow-900/10', label: 'Средний' },
    low: { icon: FiInfo, color: 'border-l-blue-400 bg-blue-50 dark:bg-blue-900/10', label: 'Низкий' },
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">
            Алерты
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Уведомления о выявленных рисках и аномалиях
          </p>
        </div>
        <div className="flex items-center gap-2">
          <FiFilter className="w-4 h-4 text-slate-400" />
          {['all', 'critical', 'high', 'medium'].map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={clsx(
                'px-3 py-1.5 rounded-lg text-xs font-medium transition-colors',
                filter === f
                  ? 'bg-blue-600 text-white'
                  : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 hover:bg-slate-200'
              )}
            >
              {f === 'all' ? 'Все' : severityConfig[f]?.label || f}
            </button>
          ))}
        </div>
      </div>

      {/* Список алертов */}
      <div className="space-y-3">
        {filteredAlerts.map((alert) => {
          const config = severityConfig[alert.severity] || severityConfig.low;
          const Icon = config.icon;

          return (
            <div
              key={alert.id}
              className={clsx(
                'border-l-4 rounded-lg p-4 transition-colors',
                config.color,
                alert.status === 'resolved' && 'opacity-60'
              )}
            >
              <div className="flex items-start gap-4">
                <Icon className="w-5 h-5 mt-0.5 flex-shrink-0" />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <h4 className="text-sm font-semibold text-slate-900 dark:text-slate-100">
                      {alert.title}
                    </h4>
                    {alert.status === 'resolved' && (
                      <span className="px-2 py-0.5 bg-green-100 text-green-700 text-xs rounded-full">
                        Решён
                      </span>
                    )}
                  </div>
                  <p className="text-sm text-slate-600 dark:text-slate-400">
                    {alert.description}
                  </p>
                  <div className="flex items-center gap-4 mt-2">
                    <span className="text-xs text-slate-500">
                      Тендер: {alert.procurement_title}
                    </span>
                    <span className="text-xs text-slate-400">
                      {new Date(alert.created_at).toLocaleString('ru-RU')}
                    </span>
                  </div>
                </div>
                {alert.status !== 'resolved' && (
                  <button
                    onClick={() => resolveMutation.mutate(alert.id)}
                    className="flex-shrink-0 p-2 text-slate-400 hover:text-green-600 transition-colors"
                    title="Отметить как решённый"
                  >
                    <FiCheck className="w-5 h-5" />
                  </button>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
