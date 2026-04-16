import { useParams, useNavigate } from "react-router";
import {
  ArrowLeft,
  Mail,
  Phone,
  MapPin,
  Briefcase,
  GraduationCap,
  Download,
  CheckCircle2,
  XCircle,
  Star,
  Calendar,
  ExternalLink,
  TrendingUp,
  Award,
} from "lucide-react";
import { RadarChart, PolarGrid, PolarAngleAxis, Radar, ResponsiveContainer, Tooltip } from "recharts";
import { candidates, jobDescriptions } from "../data/mockData";

const statusConfig: Record<string, { label: string; color: string }> = {
  shortlisted: { label: "Shortlisted", color: "text-emerald-700 bg-emerald-50 border border-emerald-200" },
  reviewing: { label: "Under Review", color: "text-amber-700 bg-amber-50 border border-amber-200" },
  rejected: { label: "Rejected", color: "text-red-600 bg-red-50 border border-red-200" },
  pending: { label: "Pending", color: "text-gray-600 bg-gray-100" },
};

export function CandidateDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const candidate = candidates.find((c) => c.id === id);

  if (!candidate) {
    return (
      <div className="p-6 text-center">
        <p className="text-gray-500">Candidate not found</p>
        <button onClick={() => navigate("/results")} className="mt-4 text-violet-600 text-sm">
          ← Back to Results
        </button>
      </div>
    );
  }

  const job = jobDescriptions.find((j) => j.id === candidate.appliedFor);
  const cfg = statusConfig[candidate.status];
  const scoreColor =
    candidate.matchScore >= 85
      ? "#10b981"
      : candidate.matchScore >= 70
      ? "#f59e0b"
      : "#ef4444";

  // Radar chart data for skill categories
  const radarData = [
    { subject: "Technical", A: Math.min(100, candidate.matchScore + 5) },
    { subject: "Experience", A: Math.min(100, (candidate.experience / 10) * 100) },
    { subject: "Education", A: candidate.education.includes("Ph.D") ? 100 : candidate.education.includes("M.S") ? 85 : 70 },
    { subject: "Skills Match", A: Math.round((candidate.skillsMatched.length / (candidate.skillsMatched.length + candidate.skillsMissing.length)) * 100) },
    { subject: "Seniority", A: Math.min(100, candidate.experience * 12) },
    { subject: "Overall Fit", A: candidate.matchScore },
  ];

  return (
    <div className="p-4 lg:p-6 max-w-5xl">
      {/* Back button */}
      <button
        onClick={() => navigate("/results")}
        className="flex items-center gap-2 text-gray-500 hover:text-gray-700 text-sm mb-5 transition-colors"
        style={{ fontWeight: 500 }}
      >
        <ArrowLeft size={16} /> Back to Candidates
      </button>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        {/* Left column - Profile card */}
        <div className="space-y-4">
          {/* Profile */}
          <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-5 text-center">
            <div className="relative inline-block mb-3">
              <div
                className="w-20 h-20 rounded-2xl flex items-center justify-center text-white text-2xl mx-auto"
                style={{
                  background: "linear-gradient(135deg, #7c3aed, #9333ea)",
                  fontWeight: 700,
                }}
              >
                {candidate.name.split(" ").map((n) => n[0]).join("")}
              </div>
              <div
                className="absolute -bottom-1 -right-1 w-6 h-6 rounded-full flex items-center justify-center text-white text-xs"
                style={{ background: scoreColor, fontWeight: 700 }}
              >
                ✓
              </div>
            </div>
            <h2 className="text-gray-900" style={{ fontWeight: 700, fontSize: "1rem" }}>
              {candidate.name}
            </h2>
            <p className="text-gray-500 text-sm mt-0.5">{candidate.currentRole}</p>

            <div className="mt-3">
              <span className={`inline-flex px-3 py-1 rounded-full text-xs ${cfg.color}`} style={{ fontWeight: 600 }}>
                {cfg.label}
              </span>
            </div>

            {/* Score ring */}
            <div className="flex items-center justify-center mt-4">
              <div className="relative w-24 h-24">
                <svg className="w-24 h-24 -rotate-90" viewBox="0 0 96 96">
                  <circle cx="48" cy="48" r="38" fill="none" stroke="#f3f4f6" strokeWidth="8" />
                  <circle
                    cx="48"
                    cy="48"
                    r="38"
                    fill="none"
                    stroke={scoreColor}
                    strokeWidth="8"
                    strokeLinecap="round"
                    strokeDasharray={`${(candidate.matchScore / 100) * 239} 239`}
                  />
                </svg>
                <div className="absolute inset-0 flex flex-col items-center justify-center">
                  <span style={{ fontSize: "1.5rem", fontWeight: 800, color: scoreColor }}>
                    {candidate.matchScore}%
                  </span>
                  <span className="text-gray-400 text-xs">Match</span>
                </div>
              </div>
            </div>

            {/* Stars */}
            <div className="flex items-center justify-center gap-1 mt-2">
              {[1, 2, 3, 4, 5].map((s) => (
                <Star
                  key={s}
                  size={16}
                  className={s <= Math.floor(candidate.matchScore / 20) ? "text-yellow-400 fill-yellow-400" : "text-gray-200 fill-gray-200"}
                />
              ))}
            </div>
          </div>

          {/* Contact */}
          <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-5 space-y-3">
            <h3 className="text-gray-700 text-sm" style={{ fontWeight: 600 }}>Contact Info</h3>
            {[
              { icon: Mail, value: candidate.email },
              { icon: Phone, value: candidate.phone },
              { icon: MapPin, value: candidate.location },
              { icon: Briefcase, value: `${candidate.experience} years experience` },
              { icon: GraduationCap, value: candidate.education },
              { icon: Calendar, value: `Screened on ${candidate.screened}` },
            ].map(({ icon: Icon, value }) => (
              <div key={value} className="flex items-start gap-2.5">
                <Icon size={14} className="text-violet-400 mt-0.5 flex-shrink-0" />
                <span className="text-gray-600 text-xs leading-relaxed">{value}</span>
              </div>
            ))}
          </div>

          {/* Action buttons */}
          <div className="space-y-2">
            <button className="w-full flex items-center justify-center gap-2 py-2.5 px-4 bg-gradient-to-r from-violet-600 to-purple-600 text-white rounded-xl text-sm shadow-md shadow-violet-200 hover:from-violet-700 hover:to-purple-700 transition-all" style={{ fontWeight: 600 }}>
              <Mail size={15} /> Send Interview Invite
            </button>
            <button className="w-full flex items-center justify-center gap-2 py-2.5 px-4 bg-white border border-gray-200 text-gray-600 rounded-xl text-sm hover:bg-gray-50 transition-colors" style={{ fontWeight: 500 }}>
              <Download size={15} /> Download Resume
            </button>
          </div>
        </div>

        {/* Right column */}
        <div className="lg:col-span-2 space-y-4">
          {/* Summary */}
          <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-5">
            <h3 className="text-gray-900 text-sm mb-3" style={{ fontWeight: 600 }}>AI Summary</h3>
            <p className="text-gray-600 text-sm leading-relaxed">{candidate.summary}</p>

            <div className="mt-4">
              <h4 className="text-gray-700 text-xs mb-2" style={{ fontWeight: 600 }}>Key Highlights</h4>
              <div className="space-y-2">
                {candidate.keyHighlights.map((h, i) => (
                  <div key={i} className="flex items-start gap-2.5">
                    <div className="w-5 h-5 rounded-full bg-violet-100 flex items-center justify-center flex-shrink-0 mt-0.5">
                      <Award size={11} className="text-violet-600" />
                    </div>
                    <p className="text-gray-600 text-sm">{h}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Skills Analysis */}
          <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-5">
            <h3 className="text-gray-900 text-sm mb-4" style={{ fontWeight: 600 }}>Skills Analysis</h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <div className="flex items-center gap-2 mb-2">
                  <CheckCircle2 size={14} className="text-emerald-500" />
                  <span className="text-emerald-700 text-xs" style={{ fontWeight: 600 }}>
                    Matched Skills ({candidate.skillsMatched.length})
                  </span>
                </div>
                <div className="flex flex-wrap gap-1.5">
                  {candidate.skillsMatched.map((skill) => (
                    <span
                      key={skill}
                      className="px-2.5 py-1 bg-emerald-50 text-emerald-700 text-xs rounded-full border border-emerald-100"
                      style={{ fontWeight: 500 }}
                    >
                      {skill}
                    </span>
                  ))}
                </div>
              </div>
              <div>
                <div className="flex items-center gap-2 mb-2">
                  <XCircle size={14} className="text-red-400" />
                  <span className="text-red-600 text-xs" style={{ fontWeight: 600 }}>
                    Missing Skills ({candidate.skillsMissing.length})
                  </span>
                </div>
                {candidate.skillsMissing.length === 0 ? (
                  <p className="text-emerald-600 text-xs bg-emerald-50 p-2 rounded-lg">
                    🎉 All required skills matched!
                  </p>
                ) : (
                  <div className="flex flex-wrap gap-1.5">
                    {candidate.skillsMissing.map((skill) => (
                      <span
                        key={skill}
                        className="px-2.5 py-1 bg-red-50 text-red-500 text-xs rounded-full border border-red-100"
                        style={{ fontWeight: 500 }}
                      >
                        {skill}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* Skill match bar */}
            <div className="mt-4">
              <div className="flex items-center justify-between mb-1.5">
                <span className="text-xs text-gray-500">Overall skill match</span>
                <span className="text-xs" style={{ fontWeight: 600, color: scoreColor }}>
                  {Math.round(
                    (candidate.skillsMatched.length /
                      (candidate.skillsMatched.length + candidate.skillsMissing.length)) *
                      100
                  )}
                  %
                </span>
              </div>
              <div className="h-2.5 bg-gray-100 rounded-full overflow-hidden">
                <div
                  className="h-full rounded-full transition-all duration-1000"
                  style={{
                    width: `${Math.round(
                      (candidate.skillsMatched.length /
                        (candidate.skillsMatched.length + candidate.skillsMissing.length)) *
                        100
                    )}%`,
                    background: `linear-gradient(90deg, ${scoreColor}, ${scoreColor}99)`,
                  }}
                />
              </div>
            </div>
          </div>

          {/* Radar Chart */}
          <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-5">
            <h3 className="text-gray-900 text-sm mb-4" style={{ fontWeight: 600 }}>
              Candidate Profile Radar
            </h3>
            <ResponsiveContainer width="100%" height={220}>
              <RadarChart data={radarData}>
                <PolarGrid stroke="#f3f4f6" />
                <PolarAngleAxis dataKey="subject" tick={{ fontSize: 11, fill: "#6b7280" }} />
                <Radar
                  name={candidate.name}
                  dataKey="A"
                  stroke="#7c3aed"
                  fill="#7c3aed"
                  fillOpacity={0.2}
                  strokeWidth={2}
                />
                <Tooltip
                  contentStyle={{
                    background: "white",
                    border: "1px solid #e5e7eb",
                    borderRadius: "8px",
                    fontSize: "12px",
                  }}
                />
              </RadarChart>
            </ResponsiveContainer>
          </div>

          {/* Applied for */}
          {job && (
            <div className="bg-gradient-to-br from-violet-50 to-purple-50 rounded-2xl border border-violet-100 p-5">
              <h3 className="text-gray-900 text-sm mb-3" style={{ fontWeight: 600 }}>
                Applied For
              </h3>
              <div className="flex items-start justify-between gap-3">
                <div>
                  <p className="text-violet-700" style={{ fontWeight: 600, fontSize: "0.9rem" }}>
                    {job.title}
                  </p>
                  <p className="text-gray-500 text-xs mt-0.5">
                    {job.department} · {job.location} · {job.type}
                  </p>
                  <div className="flex flex-wrap gap-1.5 mt-2">
                    {job.requiredSkills.slice(0, 5).map((s) => (
                      <span key={s} className="px-2 py-0.5 bg-white text-violet-600 text-xs rounded-full border border-violet-200" style={{ fontWeight: 500 }}>
                        {s}
                      </span>
                    ))}
                  </div>
                </div>
                <TrendingUp size={18} className="text-violet-400 flex-shrink-0" />
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
