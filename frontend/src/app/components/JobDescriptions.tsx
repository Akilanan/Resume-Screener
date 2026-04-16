import { useState } from "react";
import { useNavigate } from "react-router";
import {
  Plus,
  Briefcase,
  MapPin,
  Users,
  Clock,
  ChevronRight,
  Search,
  Edit3,
  Trash2,
  CheckCircle2,
  XCircle,
  FileText,
  Zap,
} from "lucide-react";
import { jobDescriptions } from "../data/mockData";

const statusConfig = {
  active: { label: "Active", color: "text-emerald-700 bg-emerald-50 border border-emerald-200", dot: "bg-emerald-400" },
  closed: { label: "Closed", color: "text-gray-500 bg-gray-100 border border-gray-200", dot: "bg-gray-400" },
  draft: { label: "Draft", color: "text-amber-700 bg-amber-50 border border-amber-200", dot: "bg-amber-400" },
};

export function JobDescriptions() {
  const navigate = useNavigate();
  const [search, setSearch] = useState("");
  const [showNewForm, setShowNewForm] = useState(false);
  const [selectedJob, setSelectedJob] = useState(jobDescriptions[0]);

  const filtered = jobDescriptions.filter(
    (j) =>
      j.title.toLowerCase().includes(search.toLowerCase()) ||
      j.department.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="p-4 lg:p-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-5">
        <div>
          <h1 className="text-gray-900" style={{ fontWeight: 700, fontSize: "1.375rem" }}>
            Job Postings
          </h1>
          <p className="text-gray-500 text-sm mt-0.5">
            Manage your active positions and job descriptions
          </p>
        </div>
        <button
          onClick={() => setShowNewForm(true)}
          className="flex items-center gap-2 px-4 py-2.5 bg-gradient-to-r from-violet-600 to-purple-600 text-white rounded-xl text-sm shadow-lg shadow-violet-200 hover:from-violet-700 hover:to-purple-700 transition-all"
          style={{ fontWeight: 600 }}
        >
          <Plus size={15} /> New Job Posting
        </button>
      </div>

      {/* Stats row */}
      <div className="grid grid-cols-3 gap-3 mb-5">
        {[
          { label: "Active", count: jobDescriptions.filter((j) => j.status === "active").length, color: "text-emerald-600", bg: "bg-emerald-50" },
          { label: "Total Screened", count: jobDescriptions.reduce((a, j) => a + j.candidatesScreened, 0), color: "text-violet-600", bg: "bg-violet-50" },
          { label: "Closed", count: jobDescriptions.filter((j) => j.status === "closed").length, color: "text-gray-500", bg: "bg-gray-50" },
        ].map((s) => (
          <div key={s.label} className="bg-white rounded-xl border border-gray-100 p-3 text-center">
            <div className={`text-2xl ${s.color}`} style={{ fontWeight: 700 }}>{s.count}</div>
            <div className="text-gray-500 text-xs mt-0.5">{s.label}</div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-5 gap-5">
        {/* Job list */}
        <div className="lg:col-span-2 space-y-3">
          {/* Search */}
          <div className="relative">
            <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
            <input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search positions..."
              className="w-full pl-9 pr-4 py-2.5 text-sm bg-white border border-gray-200 rounded-xl outline-none focus:border-violet-400 focus:ring-2 focus:ring-violet-100 transition-all"
            />
          </div>

          {filtered.map((job) => {
            const cfg = statusConfig[job.status];
            const isSelected = selectedJob?.id === job.id;

            return (
              <div
                key={job.id}
                onClick={() => setSelectedJob(job)}
                className={`bg-white rounded-xl border p-4 cursor-pointer transition-all ${
                  isSelected
                    ? "border-violet-300 shadow-md shadow-violet-100"
                    : "border-gray-100 shadow-sm hover:border-violet-200 hover:shadow-md"
                }`}
              >
                <div className="flex items-start justify-between gap-2 mb-2">
                  <div className="w-8 h-8 rounded-lg bg-violet-50 flex items-center justify-center flex-shrink-0">
                    <Briefcase size={15} className="text-violet-600" />
                  </div>
                  <span className={`text-xs px-2 py-0.5 rounded-full ${cfg.color}`} style={{ fontWeight: 500 }}>
                    {cfg.label}
                  </span>
                </div>
                <h3 className="text-gray-900 text-sm" style={{ fontWeight: 600 }}>
                  {job.title}
                </h3>
                <p className="text-gray-400 text-xs mt-0.5">{job.department}</p>

                <div className="flex items-center gap-3 mt-3">
                  <span className="flex items-center gap-1 text-xs text-gray-400">
                    <MapPin size={10} /> {job.location}
                  </span>
                  <span className="flex items-center gap-1 text-xs text-violet-500" style={{ fontWeight: 600 }}>
                    <Users size={10} /> {job.candidatesScreened} screened
                  </span>
                </div>
              </div>
            );
          })}
        </div>

        {/* Job detail */}
        {selectedJob && (
          <div className="lg:col-span-3 bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
            <div className="p-5 border-b border-gray-50">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <div className="flex items-center gap-2 mb-2">
                    <span
                      className={`text-xs px-2.5 py-0.5 rounded-full ${statusConfig[selectedJob.status].color}`}
                      style={{ fontWeight: 500 }}
                    >
                      {statusConfig[selectedJob.status].label}
                    </span>
                    <span className="text-xs text-gray-400">{selectedJob.type}</span>
                  </div>
                  <h2 className="text-gray-900" style={{ fontWeight: 700, fontSize: "1.1rem" }}>
                    {selectedJob.title}
                  </h2>
                  <div className="flex items-center gap-4 mt-1">
                    <span className="flex items-center gap-1 text-xs text-gray-500">
                      <Briefcase size={12} /> {selectedJob.department}
                    </span>
                    <span className="flex items-center gap-1 text-xs text-gray-500">
                      <MapPin size={12} /> {selectedJob.location}
                    </span>
                    <span className="flex items-center gap-1 text-xs text-gray-500">
                      <Clock size={12} /> Posted {selectedJob.createdAt}
                    </span>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <button className="p-2 rounded-lg hover:bg-gray-100 text-gray-400 hover:text-gray-600 transition-colors">
                    <Edit3 size={14} />
                  </button>
                  <button className="p-2 rounded-lg hover:bg-red-50 text-gray-400 hover:text-red-500 transition-colors">
                    <Trash2 size={14} />
                  </button>
                </div>
              </div>
            </div>

            <div className="p-5 space-y-5 overflow-y-auto" style={{ maxHeight: "calc(100vh - 280px)" }}>
              {/* Description */}
              <div>
                <h3 className="text-gray-700 text-sm mb-2" style={{ fontWeight: 600 }}>Description</h3>
                <p className="text-gray-600 text-sm leading-relaxed">{selectedJob.description}</p>
              </div>

              {/* Requirements */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <h3 className="text-gray-700 text-sm mb-2" style={{ fontWeight: 600 }}>Experience</h3>
                  <p className="text-gray-600 text-sm">{selectedJob.experience}</p>
                </div>
                <div>
                  <h3 className="text-gray-700 text-sm mb-2" style={{ fontWeight: 600 }}>Education</h3>
                  <p className="text-gray-600 text-sm">{selectedJob.education}</p>
                </div>
              </div>

              {/* Required Skills */}
              <div>
                <div className="flex items-center gap-2 mb-2">
                  <CheckCircle2 size={14} className="text-emerald-500" />
                  <h3 className="text-gray-700 text-sm" style={{ fontWeight: 600 }}>
                    Required Skills
                  </h3>
                </div>
                <div className="flex flex-wrap gap-2">
                  {selectedJob.requiredSkills.map((skill) => (
                    <span
                      key={skill}
                      className="px-3 py-1 bg-emerald-50 text-emerald-700 text-xs rounded-full border border-emerald-100"
                      style={{ fontWeight: 500 }}
                    >
                      {skill}
                    </span>
                  ))}
                </div>
              </div>

              {/* Nice to have */}
              <div>
                <div className="flex items-center gap-2 mb-2">
                  <FileText size={14} className="text-blue-400" />
                  <h3 className="text-gray-700 text-sm" style={{ fontWeight: 600 }}>
                    Nice to Have
                  </h3>
                </div>
                <div className="flex flex-wrap gap-2">
                  {selectedJob.niceToHave.map((skill) => (
                    <span
                      key={skill}
                      className="px-3 py-1 bg-blue-50 text-blue-600 text-xs rounded-full border border-blue-100"
                      style={{ fontWeight: 500 }}
                    >
                      {skill}
                    </span>
                  ))}
                </div>
              </div>

              {/* Screening stats */}
              <div className="bg-gradient-to-br from-violet-50 to-purple-50 rounded-xl p-4 border border-violet-100">
                <div className="flex items-center gap-2 mb-3">
                  <Zap size={14} className="text-violet-600" />
                  <h3 className="text-violet-700 text-sm" style={{ fontWeight: 600 }}>Screening Stats</h3>
                </div>
                <div className="grid grid-cols-3 gap-3">
                  {[
                    { label: "Screened", value: selectedJob.candidatesScreened },
                    { label: "Shortlisted", value: Math.floor(selectedJob.candidatesScreened * 0.3) },
                    { label: "Avg Score", value: "79%" },
                  ].map((s) => (
                    <div key={s.label} className="text-center">
                      <div className="text-violet-700" style={{ fontWeight: 700, fontSize: "1.1rem" }}>
                        {s.value}
                      </div>
                      <div className="text-violet-500 text-xs mt-0.5">{s.label}</div>
                    </div>
                  ))}
                </div>
              </div>

              {/* CTA */}
              <div className="flex gap-2">
                <button
                  onClick={() => navigate("/screen")}
                  className="flex-1 flex items-center justify-center gap-2 py-2.5 px-4 bg-gradient-to-r from-violet-600 to-purple-600 text-white rounded-xl text-sm shadow-md shadow-violet-200 hover:from-violet-700 hover:to-purple-700 transition-all"
                  style={{ fontWeight: 600 }}
                >
                  <Zap size={14} /> Screen Resumes for This Job
                </button>
                <button
                  onClick={() => navigate("/results")}
                  className="flex items-center gap-2 py-2.5 px-4 bg-white border border-gray-200 text-gray-600 rounded-xl text-sm hover:bg-gray-50 transition-colors"
                  style={{ fontWeight: 500 }}
                >
                  <Users size={14} /> View Candidates
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
