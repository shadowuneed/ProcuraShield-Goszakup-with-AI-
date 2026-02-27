'use client';

import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';

interface TrendChartProps {
  data?: Array<{ date: string; count: number; high_risk: number }>;
}

export function TrendChart({ data }: TrendChartProps) {
  const chartData = data || [
    { date: '01.01', count: 45, high_risk: 3 },
    { date: '02.01', count: 52, high_risk: 5 },
    { date: '03.01', count: 38, high_risk: 2 },
    { date: '04.01', count: 67, high_risk: 8 },
    { date: '05.01', count: 55, high_risk: 4 },
    { date: '06.01', count: 73, high_risk: 7 },
    { date: '07.01', count: 61, high_risk: 6 },
  ];

  return (
    <div className="bg-white dark:bg-slate-800 rounded-xl p-5 shadow-sm border border-slate-200 dark:border-slate-700">
      <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-100 mb-4">
        Динамика закупок
      </h3>
      <ResponsiveContainer width="100%" height={300}>
        <AreaChart data={chartData}>
          <defs>
            <linearGradient id="colorCount" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
              <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
            </linearGradient>
            <linearGradient id="colorRisk" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#ef4444" stopOpacity={0.3} />
              <stop offset="95%" stopColor="#ef4444" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
          <XAxis dataKey="date" stroke="#94a3b8" fontSize={12} />
          <YAxis stroke="#94a3b8" fontSize={12} />
          <Tooltip
            contentStyle={{
              backgroundColor: '#1e293b',
              border: 'none',
              borderRadius: '8px',
              color: '#f8fafc',
            }}
          />
          <Area
            type="monotone"
            dataKey="count"
            name="Всего"
            stroke="#3b82f6"
            fill="url(#colorCount)"
            strokeWidth={2}
          />
          <Area
            type="monotone"
            dataKey="high_risk"
            name="Высокий риск"
            stroke="#ef4444"
            fill="url(#colorRisk)"
            strokeWidth={2}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
