import { useState, useEffect } from "react";
import { useNavigate } from "react-router";
import {
  Search,
  SlidersHorizontal,
  CheckCircle2,
  XCircle,
  AlertCircle,
  ChevronRight,
  MapPin,
  Briefcase,
  GraduationCap,
  Star,
  Download,
  Mail,
  RefreshCw,
} from "lucide-react";
import { candidates as mockCandidates, jobDescriptions } from "../data/mockData";
import { fetchResults, type ScreeningResult } from "../services/api";

type FilterStatus = "all" | "shortlisted" | "reviewing" | "rejected";

const statusConfig = {
  shortlisted: {
    label: "Shortlisted",
    color: "text-emerald-700 bg-emerald-50 border-emerald-200",
    icon: CheckCircle2,
  },
  reviewing: {
    label: "Reviewing",
    color: "text-amber-700 bg-amber-50 border-amber-200",
    icon: AlertCircle,
  },
  rejected: {
    label: "Rejected",
    color: "text-red-600 bg-red-50 border-red-200",
    icon: XCircle,
  },
  pending: {
    label: "Pending",
    color: "text-gray-600 bg-gray-100 border-gray-200",
    icon: AlertCircle,
  },
};

const scoreColor = (score: number) => {
  if (score >= 85) return { text: "text-emerald-600", stroke: "#10b981", ring: "ring-emerald-100" };
  if (score >= 70) return { text: "text-amber-600", stroke: "#f59e0b", ring: "ring-amber-100" };
  return { text: "text-red-500", stroke: "#ef4444", ring: "ring-red-100" };
};

// Derive status from match score
function scoreToStatus(score: number): "shortlisted" | "reviewing" | "rejected" {
  if (score >= 80) return "shortlisted";
  if (score >= 65) return "reviewing";
  return "rejected";
}

// Map API result to display candidate shape
function apiResultToCandidate(r: ScreeningResult, index: number) {
  return {
    id: `api-${index}`,
    name: r.name || r.filename.replace(/\.[^/.]+$/, "").replace(/[_-]/g, " "),
    email: r.email || "—",
    phone: r.phone || "—",
    location: "—",
    experience: r.experience || 0,
    education: r.education || "—",
    currentRole: "—",
    matchScore: r.match_score,
    skillsMatched: r.matched_skills || [],
    skillsMissing: r.missing_skills || [],
    summary: r.summary || "",
    resumeFile: r.filename,
    appliedFor: "",
    screened: new Date().toISOString().split("T")[0],
    status: scoreToStatus(r.match_score) as "shortlisted" | "reviewing" | "rejected" | "pending",
    keyHighlights: [],
  };
}

export function Results() {
  const navigate = useNavigate();
  const [search, setSearch] = useState("");
  const [filterStatus, setFilterStatus] = useState<FilterStatus>("all");
  const [filterJob, setFilterJob] = useState("all");
  const [sortBy, setSortBy] = useState<"score" | "name" | "date">("score");
  const [dataSource, setDataSource] = useState<"mock" | "api" | "session">("mock");
  const [candidates, setCandidates] = useState(mockCandidates as any[]);
  const [isRefreshing, setIsRefreshing] = useState(false);

  // Check for session-stored screening results (from ScreenResumes page)
  useEffect(() => {
    const stored = sessionStorage.getItem("screeningResults");
    if (stored) {
      try {
        const parsed: ScreeningResult[] = JSON.parse(stored);
        if (parsed.length > 0) {
          setCandidates(parsed.map(apiResultToCandidate));
          setDataSource("session");
          return;
        }
      } catch {}
    }
    // Attempt to load from live API
    loadFromApi();
  }, []);

  async function loadFromApi() {
    setIsRefreshing(true);
    try {
      const data = await fetchResults();
      if (data && data.length > 0) {
        const all = data.flatMap((batch, bi) =>
          batch.results.map((r, ri) => apiResultToCandidate(r, bi * 100 + ri))
        );
        if (all.length > 0) {
          setCandidates(all);
          setDataSource("api");
        }
      }
    } catch {
      // Stay on mock data silently
    } finally {
      setIsRefreshing(false);
    }
  }

  const filtered = candidates
    .filter((c) => {
      const matchesSearch =
        c.name.toLowerCase().includes(search.toLowerCase()) ||
        (c.currentRole || "").toLowerCase().includes(search.toLowerCase()) ||
        c.skillsMatched.some((s: string) => s.toLowerCase().includes(search.toLowerCase()));
      const matchesStatus = filterStatus === "all" || c.status === filterStatus;
      const matchesJob = filterJob === "all" || c.appliedFor === filterJob;
      return matchesSearch && matchesStatus && matchesJob;
    })
    .sort((a, b) => {
      if (sortBy === "score") return b.matchScore - a.matchScore;
      if (sortBy === "name") return a.name.localeCompare(b.name);
      return new Date(b.screened).getTime() - new Date(a.screened).getTime();
    });

  const statusCounts = {
    all: candidates.length,
    shortlisted: candidates.filter((c) => c.status === "shortlisted").length,
    reviewing: candidates.filter((c) => c.status === "reviewing").length,
    rejected: candidates.filter((c) => c.status === "rejected").length,
  };

  return (
    <div className="p-4 lg:p-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-5">
        <div>
          <h1 className="text-gray-900" style={{ fontWeight: 700, fontSize: "1.375rem" }}>
            Candidates
          </h1>
          <div className="flex items-center gap-2 mt-0.5">
            <p className="text-gray-500 text-sm">
              {candidates.length} candidates screened
            </p>
            {dataSource === "session" && (
              <span className="text-xs px-2 py-0.5 rounded-full bg-violet-100 text-violet-600 border border-violet-200" style={{ fontWeight: 500 }}>
                Latest Batch
              </span>
            )}
            {dataSource === "api" && (
              <span className="text-xs px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-600 border border-emerald-200" style={{ fontWeight: 500 }}>
                Live from API
              </span>
            )}
            {dataSource === "mock" && (
              <span className="text-xs px-2 py-0.5 rounded-full bg-gray-100 text-gray-500 border border-gray-200" style={{ fontWeight: 500 }}>
                Demo Data
              </span>
            )}
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={loadFromApi}
            disabled={isRefreshing}
            className="flex items-center gap-2 px-3 py-2 text-sm text-gray-600 bg-white border border-gray-200 rounded-xl hover:bg-gray-50 transition-colors"
          >
            <RefreshCw size={14} className={isRefreshing ? "animate-spin" : ""} />
            Refresh
          </button>
          <button className="flex items-center gap-2 px-3 py-2 text-sm text-gray-600 bg-white border border-gray-200 rounded-xl hover:bg-gray-50 transition-colors">
            <Download size={14} />
            Export
          </button>
        </div>
      </div>

      {/* Filter tabs */}
      <div className="flex items-center gap-1 mb-4 overflow-x-auto pb-1">
        {(["all", "shortlisted", "reviewing", "rejected"] as FilterStatus[]).map((status) => (
          <button
            key={status}
            onClick={() => setFilterStatus(status)}
            className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm whitespace-nowrap transition-all ${
              filterStatus === status
                ? "bg-violet-600 text-white shadow-md shadow-violet-200"
                : "bg-white text-gray-500 border border-gray-200 hover:border-gray-300"
            }`}
            style={{ fontWeight: filterStatus === status ? 600 : 400 }}
          >
            {status === "all" ? "All" : status.charAt(0).toUpperCase() + status.slice(1)}
            <span
              className={`text-xs px-1.5 py-0.5 rounded-full ${
                filterStatus === status ? "bg-white/20 text-white" : "bg-gray-100 text-gray-500"
              }`}
            >
              {statusCounts[status]}
            </span>
          </button>
        ))}
      </div>

      {/* Search + Filters */}
      <div className="flex items-center gap-3 mb-5">
        <div className="flex-1 relative">
          <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search by name, role, or skill..."
            className="w-full pl-9 pr-4 py-2.5 text-sm bg-white border border-gray-200 rounded-xl outline-none focus:border-violet-400 focus:ring-2 focus:ring-violet-100 transition-all"
          />
        </div>
        {dataSource === "mock" && (
          <select
            value={filterJob}
            onChange={(e) => setFilterJob(e.target.value)}
            className="px-3 py-2.5 text-sm bg-white border border-gray-200 rounded-xl outline-none focus:border-violet-400 text-gray-600 hidden sm:block"
          >
            <option value="all">All Positions</option>
            {jobDescriptions.map((j) => (
              <option key={j.id} value={j.id}>{j.title}</option>
            ))}
          </select>
        )}
        <select
          value={sortBy}
          onChange={(e) => setSortBy(e.target.value as any)}
          className="px-3 py-2.5 text-sm bg-white border border-gray-200 rounded-xl outline-none focus:border-violet-400 text-gray-600 hidden sm:block"
        >
          <option value="score">Sort: Match Score</option>
          <option value="name">Sort: Name</option>
          <option value="date">Sort: Date</option>
        </select>
      </div>

      {/* Candidate cards */}
      <div className="space-y-3">
        {filtered.length === 0 && (
          <div className="text-center py-16 text-gray-400">
            <Search size={40} className="mx-auto mb-3 opacity-30" />
            <p className="text-sm">No candidates match your filters</p>
            <button
              onClick={() => navigate("/screen")}
              className="mt-3 text-sm text-violet-600 hover:underline"
            >
              Screen new resumes →
            </button>
          </div>
        )}

        {filtered.map((candidate, index) => {
          const sc = scoreColor(candidate.matchScore);
          const cfg = statusConfig[candidate.status] || statusConfig.pending;
          const StatusIcon = cfg.icon;
          const job = jobDescriptions.find((j) => j.id === candidate.appliedFor);

          return (
            <div
              key={candidate.id}
              onClick={() => dataSource === "mock" && navigate(`/results/${candidate.id}`)}
              className={`bg-white rounded-2xl border border-gray-100 shadow-sm hover:shadow-md hover:border-violet-100 transition-all group ${dataSource === "mock" ? "cursor-pointer" : ""}`}
            >
              <div className="flex items-start gap-4 p-4 lg:p-5">
                {/* Rank */}
                <div className="flex-shrink-0 hidden sm:flex flex-col items-center">
                  <div
                    className={`w-7 h-7 rounded-full flex items-center justify-center text-xs ${
                      index === 0
                        ? "bg-yellow-100 text-yellow-600 border border-yellow-200"
                        : index === 1
                        ? "bg-gray-100 text-gray-600"
                        : index === 2
                        ? "bg-orange-50 text-orange-500"
                        : "bg-gray-50 text-gray-400"
                    }`}
                    style={{ fontWeight: 700 }}
                  >
                    {index === 0 ? "🥇" : index === 1 ? "🥈" : index === 2 ? "🥉" : `#${index + 1}`}
                  </div>
                </div>

                {/* Avatar */}
                <div
                  className={`w-11 h-11 rounded-full flex items-center justify-center text-white text-sm flex-shrink-0 ring-2 ${sc.ring}`}
                  style={{ background: "linear-gradient(135deg, #7c3aed, #9333ea)", fontWeight: 700 }}
                >
                  {candidate.name.split(" ").map((n: string) => n[0]).join("").slice(0, 2)}
                </div>

                {/* Main info */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <h3 className="text-gray-900 text-sm" style={{ fontWeight: 600 }}>
                        {candidate.name}
                      </h3>
                      {candidate.currentRole && candidate.currentRole !== "—" && (
                        <p className="text-gray-500 text-xs mt-0.5">{candidate.currentRole}</p>
                      )}
                      {candidate.resumeFile && (
                        <p className="text-gray-400 text-xs mt-0.5">📄 {candidate.resumeFile}</p>
                      )}
                    </div>
                    <span
                      className={`flex items-center gap-1 px-2.5 py-1 rounded-full text-xs border ${cfg.color}`}
                      style={{ fontWeight: 500 }}
                    >
                      <StatusIcon size={11} />
                      {cfg.label}
                    </span>
                  </div>

                  <div className="flex flex-wrap items-center gap-3 mt-2">
                    {candidate.location && candidate.location !== "—" && (
                      <span className="flex items-center gap-1 text-xs text-gray-400">
                        <MapPin size={11} /> {candidate.location}
                      </span>
                    )}
                    {candidate.experience > 0 && (
                      <span className="flex items-center gap-1 text-xs text-gray-400">
                        <Briefcase size={11} /> {candidate.experience} yrs exp
                      </span>
                    )}
                    {candidate.education && candidate.education !== "—" && (
                      <span className="flex items-center gap-1 text-xs text-gray-400">
                        <GraduationCap size={11} /> {candidate.education.split(",")[0]}
                      </span>
                    )}
                    {job && (
                      <span className="flex items-center gap-1 text-xs text-violet-500 bg-violet-50 px-2 py-0.5 rounded-full" style={{ fontWeight: 500 }}>
                        {job.title}
                      </span>
                    )}
                  </div>

                  {/* Skills */}
                  <div className="flex flex-wrap gap-1.5 mt-2.5">
                    {candidate.skillsMatched.slice(0, 5).map((skill: string) => (
                      <span
                        key={skill}
                        className="px-2 py-0.5 bg-emerald-50 text-emerald-700 text-xs rounded-full border border-emerald-100"
                        style={{ fontWeight: 500 }}
                      >
                        ✓ {skill}
                      </span>
                    ))}
                    {candidate.skillsMissing.slice(0, 2).map((skill: string) => (
                      <span
                        key={skill}
                        className="px-2 py-0.5 bg-red-50 text-red-500 text-xs rounded-full border border-red-100"
                        style={{ fontWeight: 500 }}
                      >
                        ✗ {skill}
                      </span>
                    ))}
                    {candidate.skillsMatched.length > 5 && (
                      <span className="px-2 py-0.5 bg-gray-100 text-gray-500 text-xs rounded-full">
                        +{candidate.skillsMatched.length - 5} more
                      </span>
                    )}
                  </div>
                </div>

                {/* Score ring */}
                <div className="flex-shrink-0 flex flex-col items-center gap-1">
                  <div className="relative w-16 h-16">
                    <svg className="w-16 h-16 -rotate-90" viewBox="0 0 64 64">
                      <circle cx="32" cy="32" r="26" fill="none" stroke="#f3f4f6" strokeWidth="6" />
                      <circle
                        cx="32"
                        cy="32"
                        r="26"
                        fill="none"
                        stroke={sc.stroke}
                        strokeWidth="6"
                        strokeLinecap="round"
                        strokeDasharray={`${(candidate.matchScore / 100) * 163} 163`}
                      />
                    </svg>
                    <div className="absolute inset-0 flex items-center justify-center">
                      <span className={`text-sm ${sc.text}`} style={{ fontWeight: 700 }}>
                        {candidate.matchScore}%
                      </span>
                    </div>
                  </div>
                  <span className="text-xs text-gray-400">match</span>
                </div>

                {dataSource === "mock" && (
                  <ChevronRight size={16} className="text-gray-300 group-hover:text-violet-400 transition-colors flex-shrink-0 self-center" />
                )}
              </div>

              {/* Bottom action bar */}
              <div className="flex items-center gap-2 px-4 lg:px-5 py-3 bg-gray-50/60 border-t border-gray-50 rounded-b-2xl">
                <button
                  onClick={(e) => e.stopPropagation()}
                  className="flex items-center gap-1.5 text-xs text-gray-500 hover:text-violet-600 transition-colors px-2 py-1 rounded-lg hover:bg-violet-50"
                  style={{ fontWeight: 500 }}
                >
                  <Mail size={12} /> Contact
                </button>
                <button
                  onClick={(e) => e.stopPropagation()}
                  className="flex items-center gap-1.5 text-xs text-gray-500 hover:text-violet-600 transition-colors px-2 py-1 rounded-lg hover:bg-violet-50"
                  style={{ fontWeight: 500 }}
                >
                  <Download size={12} /> Resume
                </button>
                <div className="flex items-center gap-1 ml-auto">
                  {[1, 2, 3, 4, 5].map((star) => (
                    <Star
                      key={`star-${candidate.id}-${star}`}
                      size={13}
                      className={`cursor-pointer transition-colors ${
                        star <= Math.floor(candidate.matchScore / 20)
                          ? "text-yellow-400 fill-yellow-400"
                          : "text-gray-200"
                      }`}
                      onClick={(e) => e.stopPropagation()}
                    />
                  ))}
                </div>
                <span className="text-xs text-gray-400 ml-2">{candidate.screened}</span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
