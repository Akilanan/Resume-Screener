import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import api from "../services/api";
import Navbar from "../components/Navbar";
import { Plus, X, Briefcase, ChevronRight, FileCode } from "lucide-react";

export default function HRDashboard() {
  const [jobs, setJobs] = useState([]);
  const [showCreate, setShowCreate] = useState(false);
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    fetchJobs();
  }, []);

  const fetchJobs = async () => {
    try {
      const res = await api.get("/jobs/");
      setJobs(res.data);
    } catch (err) {
      console.error(err);
    }
  };

  const handleCreateJob = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await api.post("/jobs/", { title, description });
      setTitle("");
      setDescription("");
      setShowCreate(false);
      fetchJobs();
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-bg-dark flex flex-col">
      <Navbar />

      <main className="flex-1 p-8 max-w-7xl mx-auto w-full">
        <div className="flex justify-between items-end mb-8 border-b border-slate-800 pb-4">
          <div>
            <h1 className="text-3xl font-bold text-white mb-2">HR Dashboard</h1>
            <p className="text-slate-400">Manage jobs and analyze candidates instantly with AI.</p>
          </div>
          <button
            onClick={() => setShowCreate(!showCreate)}
            className="flex items-center gap-2 px-4 py-2 bg-brand-600 hover:bg-brand-500 text-white rounded-lg transition-colors shadow-lg shadow-brand-500/20"
          >
            {showCreate ? <X className="w-5 h-5" /> : <Plus className="w-5 h-5" />}
            {showCreate ? "Cancel" : "Create New Job"}
          </button>
        </div>

        {showCreate && (
          <div className="glass-card p-6 mb-8 animate-in slide-in-from-top-4 fade-in duration-300">
            <h2 className="text-xl font-semibold text-white mb-4">Post a new job requirement</h2>
            <form onSubmit={handleCreateJob} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-1">Job Title</label>
                <input
                  type="text"
                  required
                  className="input-field"
                  placeholder="e.g. Senior Frontend Engineer"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-1">Job Description</label>
                <textarea
                  required
                  rows={5}
                  className="input-field max-h-[300px]"
                  placeholder="Paste the full job description here. The AI will use this to score all resumes..."
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                />
              </div>
              <div className="flex justify-end">
                <button type="submit" disabled={loading} className="px-6 py-2 bg-green-600 hover:bg-green-500 text-white rounded-lg transition-colors font-medium">
                  {loading ? "Saving..." : "Save Job Profile"}
                </button>
              </div>
            </form>
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {jobs.length === 0 && !showCreate ? (
            <div className="col-span-full text-center py-20 glass-card">
              <Briefcase className="w-12 h-12 text-slate-600 mx-auto mb-4" />
              <h3 className="text-xl font-medium text-slate-300 mb-2">No jobs created yet</h3>
              <p className="text-slate-500">Create your first job to start screening candidates.</p>
            </div>
          ) : (
            jobs.map((job) => (
              <div key={job.id} className="glass-card p-6 flex flex-col group hover:border-brand-500/50 transition-colors cursor-pointer" onClick={() => navigate(`/jobs/${job.id}`)}>
                <div className="flex justify-between items-start mb-4">
                  <div className="p-3 bg-brand-500/10 rounded-xl text-brand-400 group-hover:scale-110 transition-transform">
                    <FileCode className="w-6 h-6" />
                  </div>
                  <span className="px-2.5 py-1 text-xs font-semibold bg-blue-500/10 text-blue-400 border border-blue-500/20 rounded-full">
                    {job.status}
                  </span>
                </div>
                
                <h3 className="text-lg font-semibold text-white mb-2 line-clamp-1">{job.title}</h3>
                <p className="text-sm text-slate-400 line-clamp-2 mb-6 flex-1">
                  {job.description}
                </p>
                
                <div className="flex justify-between items-center pt-4 border-t border-slate-700/50 text-sm">
                  <span className="text-slate-500">
                    {new Date(job.created_at).toLocaleDateString()}
                  </span>
                  <div className="flex items-center text-brand-400 font-medium group-hover:translate-x-1 transition-transform">
                    View Candidates <ChevronRight className="w-4 h-4 ml-1" />
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </main>
    </div>
  );
}
