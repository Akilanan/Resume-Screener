import { useState, useEffect } from "react";
import api from "../services/api";
import Navbar from "../components/Navbar";
import { Users, Briefcase, FileText, CheckCircle } from "lucide-react";

export default function AdminPanel() {
  const [stats, setStats] = useState(null);
  const [users, setUsers] = useState([]);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [statsRes, usersRes] = await Promise.all([
          api.get("/admin/stats"),
          api.get("/admin/users")
        ]);
        setStats(statsRes.data);
        setUsers(usersRes.data);
      } catch (err) {
        console.error("Failed to fetch admin data", err);
      }
    };
    fetchData();
  }, []);

  return (
    <div className="min-h-screen bg-bg-dark flex flex-col">
      <Navbar />

      <main className="flex-1 p-8 max-w-7xl mx-auto w-full">
        <h1 className="text-3xl font-bold text-white mb-2">System Overview</h1>
        <p className="text-slate-400 mb-8">Platform statistics and user management.</p>

        {stats && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-12">
            <StatCard 
              icon={<Users className="w-8 h-8 text-blue-400" />} 
              label="Total Users" 
              value={stats.total_users} 
              colorClass="bg-blue-500/10 border-blue-500/20"
            />
            <StatCard 
              icon={<Briefcase className="w-8 h-8 text-purple-400" />} 
              label="Active Jobs" 
              value={stats.total_jobs} 
              colorClass="bg-purple-500/10 border-purple-500/20"
            />
            <StatCard 
              icon={<FileText className="w-8 h-8 text-amber-400" />} 
              label="Resumes Processed" 
              value={stats.total_resumes} 
              colorClass="bg-amber-500/10 border-amber-500/20"
            />
            <StatCard 
              icon={<CheckCircle className="w-8 h-8 text-green-400" />} 
              label="Completed Screening" 
              value={stats.completed_resumes} 
              colorClass="bg-green-500/10 border-green-500/20"
            />
          </div>
        )}

        <div className="glass-card overflow-hidden">
          <div className="px-6 py-4 border-b border-slate-800">
            <h2 className="text-xl font-semibold text-white">Registered Users</h2>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-slate-900/50">
                  <th className="px-6 py-4 text-sm font-semibold text-slate-300">ID</th>
                  <th className="px-6 py-4 text-sm font-semibold text-slate-300">Email</th>
                  <th className="px-6 py-4 text-sm font-semibold text-slate-300">Role</th>
                  <th className="px-6 py-4 text-sm font-semibold text-slate-300">Status</th>
                  <th className="px-6 py-4 text-sm font-semibold text-slate-300">MFA</th>
                  <th className="px-6 py-4 text-sm font-semibold text-slate-300">Joined</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800">
                {users.map(user => (
                  <tr key={user.id} className="hover:bg-slate-800/30 transition-colors">
                    <td className="px-6 py-4 text-sm text-slate-400 font-mono">...{user.id.slice(-8)}</td>
                    <td className="px-6 py-4 text-sm text-white">{user.email}</td>
                    <td className="px-6 py-4">
                      <span className={`px-2.5 py-1 rounded-full text-xs font-medium uppercase tracking-wider ${
                        user.role === 'admin' ? 'bg-purple-500/10 text-purple-400 border border-purple-500/20' : 'bg-slate-700/50 text-slate-300 border border-slate-600'
                      }`}>
                        {user.role}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center">
                        <div className={`w-2 h-2 rounded-full mr-2 ${user.is_active ? 'bg-green-500' : 'bg-red-500'}`}></div>
                        <span className="text-sm text-slate-300">{user.is_active ? 'Active' : 'Disabled'}</span>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <span className={`text-sm ${user.mfa_enabled ? 'text-green-400' : 'text-slate-500'}`}>
                        {user.mfa_enabled ? 'Enabled' : 'Disabled'}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-sm text-slate-400">
                      {new Date(user.created_at).toLocaleDateString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </main>
    </div>
  );
}

function StatCard({ icon, label, value, colorClass }) {
  return (
    <div className={`glass-card p-6 border ${colorClass}`}>
      <div className="flex justify-between items-start">
        <div>
          <p className="text-sm font-medium text-slate-400 mb-1">{label}</p>
          <h3 className="text-3xl font-bold text-white">{value}</h3>
        </div>
        <div className="p-3 bg-slate-900/50 rounded-xl">
          {icon}
        </div>
      </div>
    </div>
  );
}
