'use client';

import { useQuery } from '@tanstack/react-query';
import { fetchDashboardStats } from '@/lib/api';
import { StatsCards } from '@/components/dashboard/StatsCards';
import { RiskChart } from '@/components/dashboard/RiskChart';
import { RecentAlerts } from '@/components/dashboard/RecentAlerts';
import { RiskMap } from '@/components/dashboard/RiskMap';
import { TopRisky } from '@/components/dashboard/TopRisky';
import { TrendChart } from '@/components/dashboard/TrendChart';

export default function DashboardPage() {
  const { data, isLoading } = useQuery({
    queryKey: ['dashboard-stats'],
    queryFn: () => fetchDashboardStats().then((r) => r.data),
    refetchInterval: 30000, // Обновление каждые 30 сек
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Заголовок */}
      <div>
        <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">
          Панель мониторинга
        </h1>
        <p className="text-sm text-slate-500 mt-1">
          Аналитика коррупционных рисков в реальном времени
        </p>
      </div>

      {/* Карточки статистики */}
      <StatsCards stats={data} />

      {/* Графики */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <RiskChart data={data?.risk_distribution} />
        <TrendChart data={data?.trends} />
      </div>

      {/* Карта и топ-рискованные */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <RiskMap data={data?.regional} />
        </div>
        <TopRisky data={data?.top_risky} />
      </div>

      {/* Последние алерты */}
      <RecentAlerts />
    </div>
  );
}
