'use client';

import { clsx } from 'clsx';

interface TopRiskyProps {
  data?: Array<{
    id: number;
    title: string;
    organization: string;
    risk_score: number;
    risk_level: string;
  }>;
}

const defaultData = [
  { id: 1, title: 'Строительство дороги Астана-Щучинск', organization: 'АО КазАвтоЖол', risk_score: 92, risk_level: 'red' },
  { id: 2, title: 'Поставка медоборудования', organization: 'УОЗ Алматы', risk_score: 87, risk_level: 'red' },
  { id: 3, title: 'Ремонт школы №45', organization: 'Акимат Караганды', risk_score: 78, risk_level: 'orange' },
  { id: 4, title: 'Закупка ПО для ГИС', organization: 'МЦР РК', risk_score: 74, risk_level: 'orange' },
  { id: 5, title: 'Благоустройство парка', organization: 'Акимат Шымкента', risk_score: 71, risk_level: 'orange' },
];

export function TopRisky({ data }: TopRiskyProps) {
  const items = data || defaultData;

  return (
    <div className="bg-white dark:bg-slate-800 rounded-xl p-5 shadow-sm border border-slate-200 dark:border-slate-700">
      <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-100 mb-4">
        Топ рискованных закупок
      </h3>
      <div className="space-y-3">
        {items.map((item, idx) => (
          <div
            key={item.id}
            className="flex items-center gap-3 p-3 rounded-lg bg-slate-50 dark:bg-slate-700/50
                       hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors cursor-pointer"
          >
            <div className="flex-shrink-0 w-8 h-8 rounded-full bg-slate-200 dark:bg-slate-600
                            flex items-center justify-center text-sm font-bold text-slate-600 dark:text-slate-300">
              {idx + 1}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-slate-900 dark:text-slate-100 truncate">
                {item.title}
              </p>
              <p className="text-xs text-slate-500 truncate">
                {item.organization}
              </p>
            </div>
            <div
              className={clsx(
                'flex-shrink-0 px-2.5 py-1 rounded-full text-xs font-bold',
                item.risk_level === 'red' && 'bg-red-100 text-red-700',
                item.risk_level === 'orange' && 'bg-orange-100 text-orange-700',
                item.risk_level === 'yellow' && 'bg-yellow-100 text-yellow-700',
                item.risk_level === 'green' && 'bg-green-100 text-green-700'
              )}
            >
              {item.risk_score}%
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
