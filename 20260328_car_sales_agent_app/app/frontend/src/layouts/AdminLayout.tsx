import { Outlet, NavLink } from 'react-router-dom'
import { FiHome, FiActivity, FiDatabase, FiCheckCircle, FiLayers } from 'react-icons/fi'
import { LuCar } from 'react-icons/lu'
import { HiOutlineSparkles } from 'react-icons/hi2'
import clsx from 'clsx'

const navItems = [
  { to: '/admin', icon: FiHome, label: 'ダッシュボード', end: true },
  { to: '/admin/logs', icon: FiActivity, label: 'AI推論ログ', end: false },
  { to: '/admin/gateway', icon: HiOutlineSparkles, label: 'AI Gateway', end: false },
  { to: '/admin/evaluation', icon: FiCheckCircle, label: '評価管理', end: false },
  { to: '/admin/catalog', icon: FiDatabase, label: 'データカタログ', end: false },
]

export function AdminLayout() {
  return (
    <div className="flex h-screen bg-gray-50">
      {/* Sidebar */}
      <aside className="w-64 bg-slate-900 flex flex-col">
        {/* Logo */}
        <div className="h-16 flex items-center px-6 border-b border-slate-700">
          <LuCar className="w-8 h-8 text-blue-400" />
          <div className="ml-3">
            <span className="text-lg font-bold text-white">IDOM Car AI</span>
            <span className="ml-2 px-2 py-0.5 text-xs bg-slate-700 text-slate-300 rounded">
              Admin
            </span>
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 px-4 py-6 space-y-1">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) =>
                clsx(
                  'flex items-center px-4 py-3 text-sm font-medium rounded-lg transition-colors',
                  isActive
                    ? 'bg-blue-600 text-white'
                    : 'text-slate-300 hover:bg-slate-800 hover:text-white'
                )
              }
            >
              <item.icon className="w-5 h-5 mr-3" />
              {item.label}
            </NavLink>
          ))}
        </nav>

        {/* Sales Link */}
        <div className="px-4 py-4 border-t border-slate-700">
          <NavLink
            to="/sales"
            className="flex items-center px-4 py-3 text-sm font-medium text-slate-300 hover:bg-slate-800 hover:text-white rounded-lg transition-colors"
          >
            <FiLayers className="w-5 h-5 mr-3" />
            営業画面へ
          </NavLink>
        </div>

        {/* System Status */}
        <div className="px-4 py-4 border-t border-slate-700">
          <div className="px-4 py-3 bg-slate-800 rounded-lg">
            <div className="flex items-center justify-between">
              <span className="text-xs text-slate-400">System Status</span>
              <span className="flex items-center text-xs text-green-400">
                <span className="w-2 h-2 bg-green-400 rounded-full mr-1 animate-pulse"></span>
                Healthy
              </span>
            </div>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-auto">
        <Outlet />
      </main>
    </div>
  )
}
