'use client';

import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  Legend,
  Tooltip,
} from 'recharts';

interface RiskChartProps {
  data?: Record<string, number>;
}

const COLORS: Record<string, string> = {
  green: '#22c55e',
  yellow: '#eab308',
  orange: '#f97316',
  red: '#ef4444',
};

const LABELS: Record<string, string> = {
  green: 'Низкий',
  yellow: 'Средний',
  orange: 'Повышенный',
  red: 'Высокий',
};

export function RiskChart({ data }: RiskChartProps) {
  const chartData = data
    ? Object.entries(data).map(([key, value]) => ({
        name: LABELS[key] || key,
        value,
        color: COLORS[key] || '#94a3b8',
      }))
    : [
        { name: 'Низкий', value: 65, color: '#22c55e' },
        { name: 'Средний', value: 20, color: '#eab308' },
        { name: 'Повышенный', value: 10, color: '#f97316' },
        { name: 'Высокий', value: 5, color: '#ef4444' },
      ];

  return (
    <div className="bg-white dark:bg-slate-800 rounded-xl p-5 shadow-sm border border-slate-200 dark:border-slate-700">
      <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-100 mb-4">
        Распределение рисков
      </h3>
      <ResponsiveContainer width="100%" height={300}>
        <PieChart>
          <Pie
            data={chartData}
            cx="50%"
            cy="50%"
            innerRadius={60}
            outerRadius={100}
            paddingAngle={4}
            dataKey="value"
          >
            {chartData.map((entry, index) => (
              <Cell key={index} fill={entry.color} />
            ))}
          </Pie>
          <Tooltip
            formatter={(value: number) => [`${value} закупок`, '']}
            contentStyle={{
              backgroundColor: '#1e293b',
              border: 'none',
              borderRadius: '8px',
              color: '#f8fafc',
            }}
          />
          <Legend />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}
