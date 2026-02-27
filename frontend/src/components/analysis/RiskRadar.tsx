'use client';

import {
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  ResponsiveContainer,
  Tooltip,
} from 'recharts';

interface RiskRadarProps {
  features: Record<string, number>;
}

const LABELS: Record<string, string> = {
  specification: 'Спецификация',
  deadline: 'Сроки',
  price: 'Цена',
  competition: 'Конкуренция',
  transparency: 'Прозрачность',
  history: 'История',
};

export function RiskRadar({ features }: RiskRadarProps) {
  const data = Object.entries(features).map(([key, value]) => ({
    subject: LABELS[key] || key,
    value,
    fullMark: 100,
  }));

  return (
    <div className="bg-white dark:bg-slate-800 rounded-xl p-5 shadow-sm border border-slate-200 dark:border-slate-700">
      <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-100 mb-4">
        Профиль рисков
      </h3>
      <ResponsiveContainer width="100%" height={350}>
        <RadarChart cx="50%" cy="50%" outerRadius="75%" data={data}>
          <PolarGrid stroke="#475569" />
          <PolarAngleAxis
            dataKey="subject"
            tick={{ fill: '#94a3b8', fontSize: 12 }}
          />
          <PolarRadiusAxis
            angle={30}
            domain={[0, 100]}
            tick={{ fill: '#64748b', fontSize: 10 }}
          />
          <Radar
            name="Риск"
            dataKey="value"
            stroke="#ef4444"
            fill="#ef4444"
            fillOpacity={0.3}
            strokeWidth={2}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: '#1e293b',
              border: 'none',
              borderRadius: '8px',
              color: '#f8fafc',
            }}
            formatter={(value: number) => [`${value}%`, 'Уровень риска']}
          />
        </RadarChart>
      </ResponsiveContainer>
    </div>
  );
}
