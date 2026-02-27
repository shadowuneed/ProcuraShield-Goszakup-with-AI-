'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { clsx } from 'clsx';
import {
  FiHome,
  FiSearch,
  FiActivity,
  FiShare2,
  FiShield,
  FiAlertTriangle,
  FiMessageSquare,
  FiSettings,
  FiLock,
} from 'react-icons/fi';

const navigation = [
  { name: 'Дашборд', href: '/', icon: FiHome },
  { name: 'Закупки', href: '/procurements', icon: FiSearch },
  { name: 'Анализ', href: '/analysis', icon: FiActivity },
  { name: 'Граф связей', href: '/graph', icon: FiShare2 },
  { name: 'Блокчейн', href: '/blockchain', icon: FiLock },
  { name: 'Алерты', href: '/alerts', icon: FiAlertTriangle },
  { name: 'Информатор', href: '/whistleblower', icon: FiMessageSquare },
  { name: 'Безопасность', href: '/security', icon: FiShield },
  { name: 'Настройки', href: '/settings', icon: FiSettings },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="hidden lg:flex lg:flex-col lg:w-64 bg-slate-900 text-white">
      {/* Логотип */}
      <div className="flex items-center gap-3 px-6 py-5 border-b border-slate-700">
        <div className="w-10 h-10 bg-blue-600 rounded-lg flex items-center justify-center">
          <FiShield className="w-6 h-6" />
        </div>
        <div>
          <h1 className="text-lg font-bold">ProcuraShield</h1>
          <p className="text-xs text-slate-400">Anti-Corruption AI</p>
        </div>
      </div>

      {/* Навигация */}
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        {navigation.map((item) => {
          const isActive = pathname === item.href;
          return (
            <Link
              key={item.name}
              href={item.href}
              className={clsx(
                'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors',
                isActive
                  ? 'bg-blue-600 text-white'
                  : 'text-slate-300 hover:bg-slate-800 hover:text-white'
              )}
            >
              <item.icon className="w-5 h-5" />
              {item.name}
            </Link>
          );
        })}
      </nav>

      {/* Статус системы */}
      <div className="px-4 py-3 border-t border-slate-700">
        <div className="flex items-center gap-2 text-xs text-slate-400">
          <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
          Система активна
        </div>
        <p className="text-xs text-slate-500 mt-1">v1.0.0 | AI Engine Online</p>
      </div>
    </aside>
  );
}
