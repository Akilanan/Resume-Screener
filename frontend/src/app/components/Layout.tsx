import { useState } from "react";
import { Outlet, NavLink, useNavigate } from "react-router";
import {
  LayoutDashboard,
  FileSearch,
  Users,
  Briefcase,
  ChevronLeft,
  ChevronRight,
  Zap,
  Bell,
  Settings,
  LogOut,
  Menu,
  X,
} from "lucide-react";

const navItems = [
  { path: "/", icon: LayoutDashboard, label: "Dashboard" },
  { path: "/screen", icon: FileSearch, label: "Screen Resumes" },
  { path: "/results", icon: Users, label: "Candidates" },
  { path: "/jobs", icon: Briefcase, label: "Job Postings" },
];

export function Layout() {
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const navigate = useNavigate();

  const handleLogout = () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    localStorage.removeItem("role");
    navigate("/login");
  };

  return (
    <div className="flex h-screen bg-gray-50 overflow-hidden">
      {/* Mobile overlay */}
      {mobileOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-40 lg:hidden"
          onClick={() => setMobileOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={`
          fixed lg:relative z-50 lg:z-auto
          flex flex-col h-full
          bg-gradient-to-b from-[#0f0c29] via-[#1a1145] to-[#0f0c29]
          transition-all duration-300 ease-in-out
          ${collapsed ? "w-20" : "w-64"}
          ${mobileOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0"}
        `}
      >
        {/* Logo */}
        <div className="flex items-center gap-3 px-5 py-5 border-b border-white/10">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-violet-500 to-purple-600 flex items-center justify-center flex-shrink-0 shadow-lg shadow-violet-500/30">
            <Zap size={18} className="text-white" />
          </div>
          {!collapsed && (
            <div className="overflow-hidden">
              <p className="text-white text-sm leading-tight" style={{ fontWeight: 700 }}>ResumeAI</p>
              <p className="text-violet-300/70 text-xs">Smart Screener</p>
            </div>
          )}
        </div>

        {/* Navigation */}
        <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
          {navItems.map(({ path, icon: Icon, label }) => (
            <NavLink
              key={path}
              to={path}
              end={path === "/"}
              onClick={() => setMobileOpen(false)}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all duration-200 group
                ${isActive
                  ? "bg-violet-600/30 text-white border border-violet-500/30 shadow-lg shadow-violet-900/20"
                  : "text-gray-400 hover:text-white hover:bg-white/8"
                }`
              }
            >
              {({ isActive }) => (
                <>
                  <Icon
                    size={19}
                    className={`flex-shrink-0 transition-colors ${isActive ? "text-violet-300" : "text-gray-500 group-hover:text-gray-300"}`}
                  />
                  {!collapsed && (
                    <span className="text-sm truncate">{label}</span>
                  )}
                  {!collapsed && isActive && (
                    <div className="ml-auto w-1.5 h-1.5 rounded-full bg-violet-400" />
                  )}
                </>
              )}
            </NavLink>
          ))}
        </nav>

        {/* Bottom actions */}
        <div className="px-3 py-4 border-t border-white/10 space-y-1">
          <button onClick={handleLogout} className="flex items-center gap-3 px-3 py-2.5 w-full rounded-xl text-gray-400 hover:text-white hover:bg-white/8 transition-all">
            <LogOut size={19} className="flex-shrink-0" />
            {!collapsed && <span className="text-sm">Logout</span>}
          </button>

          {/* User avatar */}
          <div className={`flex items-center gap-3 px-3 py-2.5 rounded-xl mt-2 ${collapsed ? "justify-center" : ""}`}>
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-violet-400 to-purple-600 flex items-center justify-center flex-shrink-0 text-white text-xs" style={{ fontWeight: 700 }}>
              HR
            </div>
            {!collapsed && (
              <div className="flex-1 overflow-hidden">
                <p className="text-white text-xs truncate" style={{ fontWeight: 600 }}>HR Team</p>
                <p className="text-gray-500 text-xs truncate">hr@company.com</p>
              </div>
            )}
          </div>
        </div>

        {/* Collapse toggle */}
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="hidden lg:flex absolute -right-3 top-20 w-6 h-6 rounded-full bg-violet-600 items-center justify-center text-white shadow-lg hover:bg-violet-500 transition-colors z-10"
        >
          {collapsed ? <ChevronRight size={12} /> : <ChevronLeft size={12} />}
        </button>
      </aside>

      {/* Main content */}
      <div className="flex-1 flex flex-col overflow-hidden min-w-0">
        {/* Top bar */}
        <header className="bg-white border-b border-gray-200 px-4 lg:px-6 py-3.5 flex items-center gap-4 flex-shrink-0">
          <button
            className="lg:hidden p-2 rounded-lg hover:bg-gray-100 transition-colors"
            onClick={() => setMobileOpen(!mobileOpen)}
          >
            {mobileOpen ? <X size={20} /> : <Menu size={20} />}
          </button>

          <div className="flex-1">
            <h1 className="text-gray-900 text-base" style={{ fontWeight: 600 }}>AI Resume Screener</h1>
            <p className="text-gray-400 text-xs">Powered by NLP & Machine Learning</p>
          </div>

          <div className="flex items-center gap-2">
            <button className="relative p-2 rounded-lg hover:bg-gray-100 transition-colors text-gray-500">
              <Bell size={18} />
              <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-violet-500"></span>
            </button>
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-gradient-to-r from-violet-600 to-purple-600 text-white text-xs" style={{ fontWeight: 600 }}>
              <Zap size={12} />
              <span>AI Active</span>
            </div>
          </div>
        </header>

        {/* Page content */}
        <main className="flex-1 overflow-y-auto">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
