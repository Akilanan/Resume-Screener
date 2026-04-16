import { useEffect, useState } from "react";
import { useNavigate } from "react-router";
import {
  Users,
  Briefcase,
  TrendingUp,
  Clock,
  ArrowRight,
  CheckCircle2,
  XCircle,
  AlertCircle,
  ChevronRight,
  Zap,
  Target,
  BarChart3,
  FileText,
  Loader2,
} from "lucide-react";
import {
  RadialBarChart,
  RadialBar,
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Cell,
} from "recharts";
import { fetchDashboardStats, BASE_URL } from "../services/api";

const skillData = [
  { skill: "Python", count: 38 },
  { skill: "React", count: 32 },
  { skill: "AWS", count: 28 },
  { skill: "Docker", count: 24 },
  { skill: "TypeScript", count: 21 },
  { skill: "Node.js", count: 19 },
];

const scoreDistribution = [
  { name: "90-100%", value: 8, fill: "#7c3aed" },
  { name: "80-89%", value: 14, fill: "#8b5cf6" },
  { name: "70-79%", value: 18, fill: "#a78bfa" },
  { name: "60-69%", value: 13, fill: "#c4b5fd" },
  { name: "< 60%", value: 10, fill: "#ede9fe" },
];

const recentActivity = [
  { name: "Priya Sharma", score: 94, job: "Senior Full Stack Dev", time: "2h ago", status: "shortlisted" },
  { name: "Aisha Patel", score: 96, job: "ML Engineer", time: "3h ago", status: "shortlisted" },
  { name: "Sofia Rodriguez", score: 91, job: "Product Designer", time: "4h ago", status: "shortlisted" },
  { name: "James Okafor", score: 74, job: "Product Designer", time: "4h ago", status: "reviewing" },
  { name: "Elena Volkov", score: 52, job: "Senior Full Stack Dev", time: "5h ago", status: "rejected" },
];

const statusColors: Record<string, string> = {
  shortlisted: "text-emerald-600 bg-emerald-50",
  reviewing: "text-amber-600 bg-amber-50",
  rejected: "text-red-500 bg-red-50",
  pending: "text-gray-500 bg-gray-100",
};

const statusIcons: Record<string, React.ReactNode> = {
  shortlisted: <CheckCircle2 size={13} />,
  reviewing: <AlertCircle size={13} />,
  rejected: <XCircle size={13} />,
};

export function Dashboard() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState<any>(null);

  useEffect(() => {
    async function load() {
      try {
        const stats = await fetchDashboardStats();
        setData(stats);
      } catch (err) {
        console.error("Dashboard load failed:", err);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  if (loading || !data) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Loader2 className="animate-spin text-violet-600" size={32} />
      </div>
    );
  }

  const stats = [
    {
      label: "Total Screened",
      value: data.stats.total_screened,
      icon: FileText,
      color: "from-violet-500 to-purple-600",
      bg: "bg-violet-50",
      iconColor: "text-violet-600",
      change: "All time",
      changePositive: true,
    },
    {
      label: "Avg. Match Score",
      value: `${data.stats.avg_match_score}%`,
      icon: Target,
      color: "from-blue-500 to-cyan-500",
      bg: "bg-blue-50",
      iconColor: "text-blue-600",
      change: "Global average",
      changePositive: true,
    },
    {
      label: "Shortlisted",
      value: data.stats.shortlisted,
      icon: Users,
      color: "from-emerald-500 to-teal-500",
      bg: "bg-emerald-50",
      iconColor: "text-emerald-600",
      change: "Score >= 80%",
      changePositive: true,
    },
    {
      label: "Active Jobs",
      value: data.stats.active_jobs,
      icon: Briefcase,
      color: "from-orange-500 to-amber-500",
      bg: "bg-orange-50",
      iconColor: "text-orange-600",
      change: "Open positions",
      changePositive: false,
    },
  ];

  const skillData = data.skill_data;
  const recentActivity = data.recent_activity;
  const scoreDistribution = data.score_distribution;

  return (
    <div className="p-4 lg:p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-gray-900" style={{ fontWeight: 700, fontSize: "1.375rem" }}>
            Dashboard
          </h1>
          <p className="text-gray-500 text-sm mt-0.5">
            Overview of your AI-powered resume screening pipeline
          </p>
        </div>
        <button
          onClick={() => navigate("/screen")}
          className="flex items-center gap-2 px-4 py-2.5 bg-gradient-to-r from-violet-600 to-purple-600 text-white rounded-xl text-sm shadow-lg shadow-violet-200 hover:shadow-violet-300 hover:from-violet-700 hover:to-purple-700 transition-all"
          style={{ fontWeight: 600 }}
        >
          <Zap size={15} />
          Screen New Resumes
        </button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.map((stat) => {
          const Icon = stat.icon;
          return (
            <div
              key={stat.label}
              className="bg-white rounded-2xl p-4 lg:p-5 border border-gray-100 shadow-sm hover:shadow-md transition-shadow"
            >
              <div className="flex items-start justify-between mb-3">
                <div className={`p-2 rounded-xl ${stat.bg}`}>
                  <Icon size={18} className={stat.iconColor} />
                </div>
              </div>
              <div className="text-2xl text-gray-900 mb-1" style={{ fontWeight: 700 }}>
                {stat.value}
              </div>
              <div className="text-xs text-gray-500 mb-2">{stat.label}</div>
              <div
                className={`text-xs ${stat.changePositive ? "text-emerald-600" : "text-amber-600"} flex items-center gap-1`}
                style={{ fontWeight: 500 }}
              >
                <TrendingUp size={11} />
                {stat.change}
              </div>
            </div>
          );
        })}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Recent Activity */}
        <div className="lg:col-span-2 bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
          <div className="flex items-center justify-between px-5 py-4 border-b border-gray-50">
            <h2 className="text-gray-900 text-sm" style={{ fontWeight: 600 }}>
              Recent Screenings
            </h2>
            <button
              onClick={() => navigate("/results")}
              className="text-xs text-violet-600 hover:text-violet-700 flex items-center gap-1 transition-colors"
              style={{ fontWeight: 500 }}
            >
              View all <ChevronRight size={13} />
            </button>
          </div>
          <div className="divide-y divide-gray-50">
            {recentActivity.map((item, i) => (
              <div
                key={i}
                className="flex items-center gap-3 px-5 py-3.5 hover:bg-gray-50/60 transition-colors cursor-pointer"
                onClick={() => navigate("/results")}
              >
                <div className="w-9 h-9 rounded-full bg-gradient-to-br from-violet-400 to-purple-600 flex items-center justify-center text-white text-xs flex-shrink-0" style={{ fontWeight: 700 }}>
                  {item.name.split(" ").map((n) => n[0]).join("")}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-gray-800 text-sm truncate" style={{ fontWeight: 500 }}>
                    {item.name}
                  </p>
                  <p className="text-gray-400 text-xs truncate">{item.job}</p>
                </div>
                <div className="flex items-center gap-2 flex-shrink-0">
                  <div className="text-right">
                    <div
                      className="text-sm"
                      style={{
                        fontWeight: 700,
                        color: item.score >= 85 ? "#7c3aed" : item.score >= 70 ? "#f59e0b" : "#ef4444",
                      }}
                    >
                      {item.score}%
                    </div>
                    <div className="text-gray-400 text-xs">{item.time}</div>
                  </div>
                  <span
                    className={`flex items-center gap-1 px-2 py-0.5 rounded-full text-xs ${statusColors[item.status]}`}
                    style={{ fontWeight: 500 }}
                  >
                    {statusIcons[item.status]}
                    {item.status}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Top Skills */}
        <div className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
          <div className="px-5 py-4 border-b border-gray-50">
            <h2 className="text-gray-900 text-sm" style={{ fontWeight: 600 }}>
              Top Skills in Demand
            </h2>
            <p className="text-gray-400 text-xs mt-0.5">From active job postings</p>
          </div>
          <div className="p-4">
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={skillData} layout="vertical" barSize={8}>
                <XAxis type="number" tick={{ fontSize: 10, fill: "#9ca3af" }} axisLine={false} tickLine={false} />
                <YAxis
                  type="category"
                  dataKey="skill"
                  tick={{ fontSize: 11, fill: "#6b7280" }}
                  axisLine={false}
                  tickLine={false}
                  width={70}
                />
                <Tooltip
                  cursor={{ fill: "rgba(139,92,246,0.06)" }}
                  contentStyle={{
                    background: "white",
                    border: "1px solid #e5e7eb",
                    borderRadius: "8px",
                    fontSize: "12px",
                  }}
                />
                <Bar dataKey="count" radius={[0, 4, 4, 0]}>
                  {skillData.map((entry, index) => (
                    <Cell
                      key={`skill-cell-${entry.skill}`}
                      fill={index === 0 ? "#7c3aed" : index === 1 ? "#8b5cf6" : "#a78bfa"}
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Score Distribution + Active Jobs */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Score Distribution */}
        <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-5">
          <h2 className="text-gray-900 text-sm mb-4" style={{ fontWeight: 600 }}>
            Match Score Distribution
          </h2>
          <div className="flex items-center gap-4">
            <div className="flex-1 space-y-2.5">
              {scoreDistribution.map((item: any) => (
                <div key={item.name} className="flex items-center gap-3">
                  <span className="text-xs text-gray-500 w-16 flex-shrink-0">{item.name}</span>
                  <div className="flex-1 h-2 bg-gray-100 rounded-full overflow-hidden">
                    <div
                      className="h-full rounded-full transition-all"
                      style={{
                        width: data.stats.total_screened > 0 ? `${(item.value / data.stats.total_screened) * 100}%` : '0%',
                        backgroundColor: item.fill,
                      }}
                    />
                  </div>
                  <span className="text-xs text-gray-500 w-6 text-right">{item.value}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Info Banner */}
        <div className="bg-violet-600 rounded-2xl p-5 text-white relative overflow-hidden">
          <div className="relative z-10">
            <h3 className="text-lg mb-2" style={{ fontWeight: 700 }}>Quick Tip</h3>
            <p className="text-violet-100 text-sm leading-relaxed mb-4">
              Real-time analytics are refreshed every time you complete a new resume screening batch.
            </p>
            <button
              onClick={() => navigate("/screen")}
              className="px-4 py-2 bg-white text-violet-600 rounded-lg text-sm transition-colors hover:bg-violet-50"
              style={{ fontWeight: 600 }}
            >
              Start Screening
            </button>
          </div>
          <Zap className="absolute -right-4 -bottom-4 text-white/10" size={120} />
        </div>
      </div>

      {/* CTA Banner */}
      <div className="relative bg-gradient-to-r from-[#1a1145] via-[#2d1b69] to-[#1a1145] rounded-2xl p-6 overflow-hidden">
        <div className="absolute inset-0 opacity-20">
          <img
            src="https://images.unsplash.com/photo-1758518730083-4c12527b6742?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxwcm9mZXNzaW9uYWwlMjByZXN1bWUlMjBoaXJpbmclMjB0ZWFtJTIwb2ZmaWNlfGVufDF8fHx8MTc3NjMzMjU0OHww&ixlib=rb-4.1.0&q=80&w=1080"
            alt=""
            className="w-full h-full object-cover"
          />
        </div>
        <div className="relative z-10 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div>
            <p className="text-violet-300 text-xs mb-1" style={{ fontWeight: 600 }}>
              ⚡ POWERED BY AI
            </p>
            <h3 className="text-white text-base" style={{ fontWeight: 700 }}>
              Screen 100 resumes in under 3 minutes
            </h3>
            <p className="text-violet-200/70 text-sm mt-1">
              Upload your job description and resume batch to get instant rankings
            </p>
          </div>
          <button
            onClick={() => navigate("/screen")}
            className="flex items-center gap-2 px-5 py-2.5 bg-violet-500 hover:bg-violet-400 text-white rounded-xl text-sm flex-shrink-0 transition-colors"
            style={{ fontWeight: 600 }}
          >
            Get Started <ArrowRight size={15} />
          </button>
        </div>
      </div>
    </div>
  );
}