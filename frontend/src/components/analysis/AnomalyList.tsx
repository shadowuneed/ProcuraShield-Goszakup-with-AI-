'use client';

import { clsx } from 'clsx';
import { FiAlertTriangle, FiAlertCircle, FiInfo } from 'react-icons/fi';

interface Anomaly {
  type: string;
  description: string;
  severity: string;
  confidence: number;
}

interface AnomalyListProps {
  anomalies: Anomaly[];
}

const TYPE_LABELS: Record<string, string> = {
  hyperspecific_requirements: 'Гиперспецифичные требования',
  unrealistic_deadline: 'Нереалистичные сроки',
  geographic_restriction: 'Географическое ограничение',
  rare_certificate: 'Редкий сертификат',
  excessive_experience: 'Завышенный опыт',
  brand_mention: 'Указание бренда',
  restrictive_language: 'Ограничительные формулировки',
  commercial_copy: 'Копия КП',
};

const severityConfig = {
  high: { icon: FiAlertTriangle, color: 'border-red-300 bg-red-50 dark:bg-red-900/20', badge: 'bg-red-100 text-red-700' },
  medium: { icon: FiAlertCircle, color: 'border-orange-300 bg-orange-50 dark:bg-orange-900/20', badge: 'bg-orange-100 text-orange-700' },
  low: { icon: FiInfo, color: 'border-yellow-300 bg-yellow-50 dark:bg-yellow-900/20', badge: 'bg-yellow-100 text-yellow-700' },
};

export function AnomalyList({ anomalies }: AnomalyListProps) {
  return (
    <div className="bg-white dark:bg-slate-800 rounded-xl p-5 shadow-sm border border-slate-200 dark:border-slate-700">
      <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-100 mb-4">
        Обнаруженные аномалии ({anomalies.length})
      </h3>
      <div className="space-y-3 max-h-[400px] overflow-y-auto">
        {anomalies.map((anomaly, idx) => {
          const config = severityConfig[anomaly.severity as keyof typeof severityConfig] || severityConfig.low;
          const Icon = config.icon;

          return (
            <div
              key={idx}
              className={clsx(
                'p-4 rounded-lg border-l-4 transition-colors',
                config.color
              )}
            >
              <div className="flex items-start gap-3">
                <Icon className="w-5 h-5 mt-0.5 flex-shrink-0 text-current" />
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-sm font-semibold text-slate-900 dark:text-slate-100">
                      {TYPE_LABELS[anomaly.type] || anomaly.type}
                    </span>
                    <span className={clsx('px-2 py-0.5 rounded-full text-xs font-medium', config.badge)}>
                      {anomaly.severity === 'high' ? 'Высокий' : anomaly.severity === 'medium' ? 'Средний' : 'Низкий'}
                    </span>
                  </div>
                  <p className="text-sm text-slate-600 dark:text-slate-400">
                    {anomaly.description}
                  </p>
                  <div className="flex items-center gap-1 mt-2">
                    <span className="text-xs text-slate-500">Уверенность:</span>
                    <div className="w-20 h-1.5 bg-slate-200 dark:bg-slate-600 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-blue-500 rounded-full"
                        style={{ width: `${anomaly.confidence * 100}%` }}
                      />
                    </div>
                    <span className="text-xs text-slate-500">
                      {(anomaly.confidence * 100).toFixed(0)}%
                    </span>
                  </div>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
