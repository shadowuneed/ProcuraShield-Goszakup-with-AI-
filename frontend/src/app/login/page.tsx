'use client';

import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { useAuthStore } from '@/store/authStore';
import { FiShield, FiMail, FiLock } from 'react-icons/fi';
import toast from 'react-hot-toast';
import { useRouter } from 'next/navigation';

interface LoginForm {
  email: string;
  password: string;
}

export default function LoginPage() {
  const { login } = useAuthStore();
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const { register, handleSubmit, formState: { errors } } = useForm<LoginForm>();

  const onSubmit = async (data: LoginForm) => {
    setLoading(true);
    try {
      await login(data.email, data.password);
      toast.success('Вход выполнен!');
      router.push('/');
    } catch {
      toast.error('Неверный email или пароль');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50 dark:bg-slate-900 px-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-blue-600 rounded-2xl mb-4">
            <FiShield className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">
            ProcuraShield
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            AI Anti-Corruption Platform
          </p>
        </div>

        <form
          onSubmit={handleSubmit(onSubmit)}
          className="bg-white dark:bg-slate-800 rounded-2xl p-8 shadow-lg border border-slate-200 dark:border-slate-700 space-y-5"
        >
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
              Email
            </label>
            <div className="relative">
              <FiMail className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 w-4 h-4" />
              <input
                {...register('email', { required: 'Введите email' })}
                type="email"
                className="w-full pl-10 pr-4 py-2.5 bg-slate-50 dark:bg-slate-700 rounded-lg text-sm
                           border border-slate-200 dark:border-slate-600 focus:ring-2 focus:ring-blue-500 outline-none"
                placeholder="admin@procurashield.kz"
              />
            </div>
            {errors.email && (
              <p className="text-xs text-red-500 mt-1">{errors.email.message}</p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
              Пароль
            </label>
            <div className="relative">
              <FiLock className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 w-4 h-4" />
              <input
                {...register('password', { required: 'Введите пароль' })}
                type="password"
                className="w-full pl-10 pr-4 py-2.5 bg-slate-50 dark:bg-slate-700 rounded-lg text-sm
                           border border-slate-200 dark:border-slate-600 focus:ring-2 focus:ring-blue-500 outline-none"
                placeholder="••••••••"
              />
            </div>
            {errors.password && (
              <p className="text-xs text-red-500 mt-1">{errors.password.message}</p>
            )}
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700
                       disabled:opacity-50 transition-colors font-medium"
          >
            {loading ? 'Вход...' : 'Войти'}
          </button>

          <div className="text-xs text-slate-500 text-center space-y-1">
            <p className="font-medium">Демо-аккаунты:</p>
            <p>admin@procurashield.kz / admin123!</p>
            <p>analyst@procurashield.kz / analyst123!</p>
          </div>
        </form>
      </div>
    </div>
  );
}
