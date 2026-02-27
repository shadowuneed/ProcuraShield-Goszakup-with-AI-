'use client';

import { useState } from 'react';
import { FiSearch, FiBell, FiUser, FiMoon, FiSun } from 'react-icons/fi';
import { useAuthStore } from '@/store/authStore';

export function Header() {
  const [darkMode, setDarkMode] = useState(false);
  const { user, logout } = useAuthStore();

  const toggleDarkMode = () => {
    setDarkMode(!darkMode);
    document.documentElement.classList.toggle('dark');
  };

  return (
    <header className="bg-white dark:bg-slate-800 border-b border-slate-200 dark:border-slate-700 px-6 py-3">
      <div className="flex items-center justify-between">
        {/* Поиск */}
        <div className="flex-1 max-w-lg">
          <div className="relative">
            <FiSearch className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 w-4 h-4" />
            <input
              type="text"
              placeholder="Поиск закупок, поставщиков, ИНН..."
              className="w-full pl-10 pr-4 py-2 bg-slate-100 dark:bg-slate-700 rounded-lg text-sm
                         border-0 focus:ring-2 focus:ring-blue-500 outline-none
                         text-slate-900 dark:text-slate-100 placeholder-slate-400"
            />
          </div>
        </div>

        {/* Правая часть */}
        <div className="flex items-center gap-4 ml-4">
          {/* Тёмная тема */}
          <button
            onClick={toggleDarkMode}
            className="p-2 text-slate-500 hover:text-slate-700 dark:text-slate-400
                       dark:hover:text-slate-200 transition-colors"
          >
            {darkMode ? <FiSun className="w-5 h-5" /> : <FiMoon className="w-5 h-5" />}
          </button>

          {/* Уведомления */}
          <button className="relative p-2 text-slate-500 hover:text-slate-700
                             dark:text-slate-400 dark:hover:text-slate-200 transition-colors">
            <FiBell className="w-5 h-5" />
            <span className="absolute top-1 right-1 w-2.5 h-2.5 bg-red-500 rounded-full" />
          </button>

          {/* Профиль */}
          <div className="flex items-center gap-3 pl-4 border-l border-slate-200 dark:border-slate-700">
            <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center">
              <FiUser className="w-4 h-4 text-white" />
            </div>
            <div className="hidden sm:block">
              <p className="text-sm font-medium text-slate-900 dark:text-slate-100">
                {user?.full_name || 'Гость'}
              </p>
              <p className="text-xs text-slate-500">
                {user?.role || 'Не авторизован'}
              </p>
            </div>
            {user && (
              <button
                onClick={logout}
                className="text-xs text-red-500 hover:text-red-700 ml-2"
              >
                Выйти
              </button>
            )}
          </div>
        </div>
      </div>
    </header>
  );
}
