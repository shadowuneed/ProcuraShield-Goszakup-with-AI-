'use client';

import { motion } from 'framer-motion';

interface AnalysisProgressProps {
  progress: number;
}

const stages = [
  { threshold: 10, label: 'Загрузка документа...' },
  { threshold: 25, label: 'Извлечение текста...' },
  { threshold: 40, label: 'NLP-анализ спецификации...' },
  { threshold: 55, label: 'Проверка стилометрии...' },
  { threshold: 70, label: 'Анализ сговора...' },
  { threshold: 85, label: 'AML-проверка...' },
  { threshold: 95, label: 'Расчёт риск-скора...' },
  { threshold: 100, label: 'Готово!' },
];

export function AnalysisProgress({ progress }: AnalysisProgressProps) {
  const currentStage = stages.find((s) => progress <= s.threshold) || stages[stages.length - 1];

  return (
    <div className="bg-white dark:bg-slate-800 rounded-xl p-6 shadow-sm border border-slate-200 dark:border-slate-700">
      <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-100 mb-4">
        Анализ документа
      </h3>

      {/* Прогресс-бар */}
      <div className="relative w-full h-3 bg-slate-200 dark:bg-slate-700 rounded-full overflow-hidden mb-3">
        <motion.div
          className="h-full bg-gradient-to-r from-blue-500 to-blue-600 rounded-full"
          initial={{ width: 0 }}
          animate={{ width: `${progress}%` }}
          transition={{ duration: 0.5, ease: 'easeInOut' }}
        />
      </div>

      <div className="flex items-center justify-between">
        <p className="text-sm text-slate-600 dark:text-slate-400">
          {currentStage.label}
        </p>
        <p className="text-sm font-medium text-slate-900 dark:text-slate-100">
          {progress}%
        </p>
      </div>

      {/* Этапы */}
      <div className="mt-4 grid grid-cols-4 gap-2">
        {stages.slice(0, -1).map((stage, idx) => (
          <div
            key={idx}
            className={`text-xs text-center py-1 rounded ${
              progress >= stage.threshold
                ? 'text-green-600 dark:text-green-400'
                : 'text-slate-400'
            }`}
          >
            {progress >= stage.threshold ? '✓' : '○'} {stage.label.replace('...', '')}
          </div>
        ))}
      </div>
    </div>
  );
}
