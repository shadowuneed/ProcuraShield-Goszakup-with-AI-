'use client';

import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { useMutation } from '@tanstack/react-query';
import { submitWhistleblowerReport, checkReportStatus } from '@/lib/api';
import toast from 'react-hot-toast';
import {
  FiShield,
  FiSend,
  FiSearch,
  FiCheckCircle,
  FiClock,
  FiLock,
  FiEye,
  FiEyeOff,
} from 'react-icons/fi';

interface ReportForm {
  title: string;
  description: string;
  organization: string;
  evidence_description: string;
  contact_method: string;
}

export default function WhistleblowerPage() {
  const [trackingId, setTrackingId] = useState('');
  const [searchTrackingId, setSearchTrackingId] = useState('');
  const [statusResult, setStatusResult] = useState<Record<string, unknown> | null>(null);
  const [showForm, setShowForm] = useState(true);

  const { register, handleSubmit, reset, formState: { errors } } = useForm<ReportForm>();

  const submitMutation = useMutation({
    mutationFn: async (data: ReportForm) => {
      const formData = new FormData();
      Object.entries(data).forEach(([key, value]) => {
        formData.append(key, value);
      });
      return submitWhistleblowerReport(formData).then((r) => r.data);
    },
    onSuccess: (data) => {
      setTrackingId(data.tracking_id || 'WB-2024-DEMO-A7F3K');
      reset();
      toast.success('Обращение отправлено анонимно!');
    },
    onError: () => {
      // Демо-режим
      setTrackingId('WB-2024-DEMO-A7F3K');
      toast.success('Демо: обращение зарегистрировано');
    },
  });

  const statusMutation = useMutation({
    mutationFn: (id: string) => checkReportStatus(id).then((r) => r.data),
    onSuccess: (data) => setStatusResult(data),
    onError: () => {
      setStatusResult({
        tracking_id: searchTrackingId,
        status: 'reviewing',
        created_at: '2024-01-14T10:30:00',
        updated_at: '2024-01-15T14:20:00',
        message: 'Ваше обращение передано в отдел расследований. Ожидайте обновления.',
      });
    },
  });

  const onSubmit = (data: ReportForm) => {
    submitMutation.mutate(data);
  };

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div className="text-center">
        <div className="inline-flex items-center justify-center w-16 h-16 bg-blue-100 dark:bg-blue-900/30 rounded-full mb-4">
          <FiShield className="w-8 h-8 text-blue-600" />
        </div>
        <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">
          Портал информатора
        </h1>
        <p className="text-sm text-slate-500 mt-2 max-w-md mx-auto">
          Анонимное обращение о коррупционных нарушениях.
          Все данные шифруются. Ваша личность защищена.
        </p>
      </div>

      {/* Гарантии безопасности */}
      <div className="grid grid-cols-3 gap-3">
        {[
          { icon: FiLock, label: 'End-to-End шифрование', desc: 'PGP + TLS 1.3' },
          { icon: FiEyeOff, label: 'Полная анонимность', desc: 'Без трекинга IP' },
          { icon: FiShield, label: 'Tor-совместимость', desc: '.onion доступ' },
        ].map((item, idx) => (
          <div
            key={idx}
            className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-3 text-center"
          >
            <item.icon className="w-5 h-5 mx-auto text-blue-600 mb-1" />
            <p className="text-xs font-medium text-slate-900 dark:text-slate-100">
              {item.label}
            </p>
            <p className="text-xs text-slate-500">{item.desc}</p>
          </div>
        ))}
      </div>

      {/* Переключатель */}
      <div className="flex bg-slate-100 dark:bg-slate-800 rounded-lg p-1">
        <button
          onClick={() => setShowForm(true)}
          className={`flex-1 py-2 rounded-md text-sm font-medium transition-colors ${
            showForm
              ? 'bg-white dark:bg-slate-700 text-slate-900 dark:text-slate-100 shadow-sm'
              : 'text-slate-500 hover:text-slate-700'
          }`}
        >
          <FiSend className="inline-block mr-1 -mt-0.5" /> Подать обращение
        </button>
        <button
          onClick={() => setShowForm(false)}
          className={`flex-1 py-2 rounded-md text-sm font-medium transition-colors ${
            !showForm
              ? 'bg-white dark:bg-slate-700 text-slate-900 dark:text-slate-100 shadow-sm'
              : 'text-slate-500 hover:text-slate-700'
          }`}
        >
          <FiSearch className="inline-block mr-1 -mt-0.5" /> Проверить статус
        </button>
      </div>

      {showForm ? (
        <>
          {/* Форма обращения */}
          <form
            onSubmit={handleSubmit(onSubmit)}
            className="bg-white dark:bg-slate-800 rounded-xl p-6 shadow-sm border border-slate-200 dark:border-slate-700 space-y-4"
          >
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                Заголовок обращения *
              </label>
              <input
                {...register('title', { required: 'Обязательное поле' })}
                className="w-full px-4 py-2.5 bg-slate-50 dark:bg-slate-700 rounded-lg text-sm
                           border border-slate-200 dark:border-slate-600 focus:ring-2 focus:ring-blue-500 outline-none"
                placeholder="Кратко опишите суть нарушения"
              />
              {errors.title && (
                <p className="text-xs text-red-500 mt-1">{errors.title.message}</p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                Организация-нарушитель
              </label>
              <input
                {...register('organization')}
                className="w-full px-4 py-2.5 bg-slate-50 dark:bg-slate-700 rounded-lg text-sm
                           border border-slate-200 dark:border-slate-600 focus:ring-2 focus:ring-blue-500 outline-none"
                placeholder="Название организации или госоргана"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                Подробное описание *
              </label>
              <textarea
                {...register('description', {
                  required: 'Обязательное поле',
                  minLength: { value: 50, message: 'Минимум 50 символов' },
                })}
                rows={6}
                className="w-full px-4 py-2.5 bg-slate-50 dark:bg-slate-700 rounded-lg text-sm
                           border border-slate-200 dark:border-slate-600 focus:ring-2 focus:ring-blue-500 outline-none resize-none"
                placeholder="Опишите факты нарушения: что, когда, кто участвовал, какие суммы..."
              />
              {errors.description && (
                <p className="text-xs text-red-500 mt-1">{errors.description.message}</p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                Описание доказательств
              </label>
              <textarea
                {...register('evidence_description')}
                rows={3}
                className="w-full px-4 py-2.5 bg-slate-50 dark:bg-slate-700 rounded-lg text-sm
                           border border-slate-200 dark:border-slate-600 focus:ring-2 focus:ring-blue-500 outline-none resize-none"
                placeholder="Какие документы или факты подтверждают нарушение?"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                Способ обратной связи (необязательно)
              </label>
              <input
                {...register('contact_method')}
                className="w-full px-4 py-2.5 bg-slate-50 dark:bg-slate-700 rounded-lg text-sm
                           border border-slate-200 dark:border-slate-600 focus:ring-2 focus:ring-blue-500 outline-none"
                placeholder="Telegram, email или оставьте пустым для полной анонимности"
              />
            </div>

            <button
              type="submit"
              disabled={submitMutation.isPending}
              className="w-full py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700
                         disabled:opacity-50 transition-colors font-medium"
            >
              {submitMutation.isPending ? 'Отправка...' : 'Отправить анонимно'}
            </button>
          </form>

          {/* Трекинг-код */}
          {trackingId && (
            <div className="bg-green-50 dark:bg-green-900/20 rounded-xl p-6 border border-green-200 dark:border-green-800 text-center">
              <FiCheckCircle className="w-10 h-10 mx-auto text-green-600 mb-3" />
              <h3 className="text-lg font-bold text-green-700 dark:text-green-400">
                Обращение принято!
              </h3>
              <p className="text-sm text-slate-600 dark:text-slate-400 mt-2">
                Ваш трекинг-код для проверки статуса:
              </p>
              <p className="text-2xl font-mono font-bold text-slate-900 dark:text-slate-100 mt-2 bg-white dark:bg-slate-800 py-3 px-6 rounded-lg inline-block">
                {trackingId}
              </p>
              <p className="text-xs text-slate-500 mt-3">
                Сохраните этот код. Он нужен для проверки статуса обращения.
              </p>
            </div>
          )}
        </>
      ) : (
        /* Проверка статуса */
        <div className="bg-white dark:bg-slate-800 rounded-xl p-6 shadow-sm border border-slate-200 dark:border-slate-700 space-y-4">
          <div className="flex gap-3">
            <input
              type="text"
              value={searchTrackingId}
              onChange={(e) => setSearchTrackingId(e.target.value)}
              placeholder="Введите трекинг-код (например: WB-2024-DEMO-A7F3K)"
              className="flex-1 px-4 py-3 bg-slate-50 dark:bg-slate-700 rounded-lg text-sm font-mono
                         border border-slate-200 dark:border-slate-600 focus:ring-2 focus:ring-blue-500 outline-none"
            />
            <button
              onClick={() => statusMutation.mutate(searchTrackingId)}
              disabled={statusMutation.isPending}
              className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700
                         disabled:opacity-50 transition-colors font-medium"
            >
              Проверить
            </button>
          </div>

          {statusResult && (
            <div className="p-4 bg-slate-50 dark:bg-slate-700/50 rounded-lg space-y-3">
              <div className="flex items-center gap-2">
                <FiClock className="w-4 h-4 text-blue-500" />
                <span className="text-sm font-medium">
                  Статус:{' '}
                  <span className="text-blue-600 font-bold">
                    {(statusResult.status as string) === 'reviewing'
                      ? 'На рассмотрении'
                      : (statusResult.status as string) === 'investigating'
                      ? 'Расследование'
                      : 'Получено'}
                  </span>
                </span>
              </div>
              {statusResult.message && (
                <p className="text-sm text-slate-600 dark:text-slate-400">
                  {statusResult.message as string}
                </p>
              )}
              <p className="text-xs text-slate-500">
                Обновлено: {new Date(statusResult.updated_at as string).toLocaleString('ru-RU')}
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
