'use client';

import { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { useMutation } from '@tanstack/react-query';
import { api } from '@/lib/api';
import toast from 'react-hot-toast';
import { FiUploadCloud, FiFileText, FiCheckCircle, FiAlertTriangle } from 'react-icons/fi';
import { RiskRadar } from '@/components/analysis/RiskRadar';
import { AnomalyList } from '@/components/analysis/AnomalyList';
import { AnalysisProgress } from '@/components/analysis/AnalysisProgress';

interface AnalysisResult {
  risk_score: number;
  risk_level: string;
  anomalies: Array<{
    type: string;
    description: string;
    severity: string;
    confidence: number;
  }>;
  features: Record<string, number>;
  explanation: string;
}

export default function AnalysisPage() {
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [progress, setProgress] = useState(0);

  const uploadMutation = useMutation({
    mutationFn: async (file: File) => {
      const formData = new FormData();
      formData.append('file', file);

      setAnalyzing(true);
      setProgress(0);

      // Имитация прогресса
      const interval = setInterval(() => {
        setProgress((prev) => Math.min(prev + 10, 90));
      }, 500);

      try {
        const response = await api.post('/api/procurements/upload', formData, {
          headers: { 'Content-Type': 'multipart/form-data' },
        });

        const procId = response.data.id;

        // Запуск анализа
        setProgress(50);
        const analysisResponse = await api.post(`/api/analysis/analyze/${procId}`);

        clearInterval(interval);
        setProgress(100);

        return analysisResponse.data;
      } catch (error) {
        clearInterval(interval);
        throw error;
      }
    },
    onSuccess: (data) => {
      setResult(data);
      setAnalyzing(false);
      toast.success('Анализ завершён!');
    },
    onError: () => {
      setAnalyzing(false);
      setProgress(0);
      toast.error('Ошибка при анализе документа');
    },
  });

  const onDrop = useCallback(
    (acceptedFiles: File[]) => {
      if (acceptedFiles.length > 0) {
        uploadMutation.mutate(acceptedFiles[0]);
      }
    },
    [uploadMutation]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'text/xml': ['.xml'],
    },
    maxFiles: 1,
    maxSize: 50 * 1024 * 1024, // 50 MB
  });

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">
          Анализ тендерной документации
        </h1>
        <p className="text-sm text-slate-500 mt-1">
          Загрузите документ для AI-анализа коррупционных рисков
        </p>
      </div>

      {/* Drag & Drop зона */}
      <div
        {...getRootProps()}
        className={`border-2 border-dashed rounded-xl p-12 text-center cursor-pointer
          transition-colors ${
            isDragActive
              ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
              : 'border-slate-300 dark:border-slate-600 hover:border-blue-400'
          }`}
      >
        <input {...getInputProps()} />
        <FiUploadCloud className="w-12 h-12 mx-auto text-slate-400 mb-4" />
        <p className="text-lg font-medium text-slate-700 dark:text-slate-300">
          {isDragActive
            ? 'Отпустите файл здесь...'
            : 'Перетащите документ или нажмите для выбора'}
        </p>
        <p className="text-sm text-slate-500 mt-2">
          Поддерживаемые форматы: PDF, DOCX, XML (до 50 МБ)
        </p>
      </div>

      {/* Прогресс анализа */}
      {analyzing && <AnalysisProgress progress={progress} />}

      {/* Результаты анализа */}
      {result && (
        <div className="space-y-6 animate-fade-in">
          {/* Общий скор */}
          <div className="bg-white dark:bg-slate-800 rounded-xl p-6 shadow-sm border border-slate-200 dark:border-slate-700">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-xl font-bold text-slate-900 dark:text-slate-100">
                  Результат анализа
                </h2>
                <p className="text-sm text-slate-500 mt-1">{result.explanation}</p>
              </div>
              <div
                className={`flex items-center gap-3 px-6 py-3 rounded-xl text-2xl font-bold ${
                  result.risk_level === 'red'
                    ? 'bg-red-100 text-red-700'
                    : result.risk_level === 'orange'
                    ? 'bg-orange-100 text-orange-700'
                    : result.risk_level === 'yellow'
                    ? 'bg-yellow-100 text-yellow-700'
                    : 'bg-green-100 text-green-700'
                }`}
              >
                {result.risk_level === 'red' || result.risk_level === 'orange' ? (
                  <FiAlertTriangle className="w-8 h-8" />
                ) : (
                  <FiCheckCircle className="w-8 h-8" />
                )}
                {result.risk_score}/100
              </div>
            </div>
          </div>

          {/* Радар и аномалии */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <RiskRadar features={result.features} />
            <AnomalyList anomalies={result.anomalies} />
          </div>
        </div>
      )}

      {/* Демо-кнопка */}
      {!result && !analyzing && (
        <div className="text-center">
          <button
            onClick={() => {
              setResult({
                risk_score: 78,
                risk_level: 'orange',
                anomalies: [
                  { type: 'hyperspecific_requirements', description: 'Обнаружены гиперспецифичные требования: указание конкретного бренда "SAP S/4HANA"', severity: 'high', confidence: 0.92 },
                  { type: 'unrealistic_deadline', description: 'Нереалистичный срок: 15 дней на внедрение ERP-системы', severity: 'high', confidence: 0.88 },
                  { type: 'geographic_restriction', description: 'Географическое ограничение: требуется наличие офиса в г.Астана', severity: 'medium', confidence: 0.75 },
                  { type: 'rare_certificate', description: 'Требуется редкий сертификат ISO/IEC 27701:2019', severity: 'medium', confidence: 0.70 },
                  { type: 'excessive_experience', description: 'Требуется опыт 15 лет в отрасли', severity: 'low', confidence: 0.60 },
                ],
                features: {
                  specification: 85,
                  deadline: 90,
                  price: 45,
                  competition: 70,
                  transparency: 55,
                  history: 65,
                },
                explanation: 'Высокий корупционный риск — обнаружено 5 аномалий, включая гиперспецифичные требования и нереалистичные сроки.',
              });
            }}
            className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium"
          >
            <FiFileText className="inline-block mr-2 -mt-0.5" />
            Запустить демо-анализ
          </button>
        </div>
      )}
    </div>
  );
}
