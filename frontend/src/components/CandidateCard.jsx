import { Check, X, AlertTriangle } from "lucide-react";

export default function CandidateCard({ candidate }) {
  const { filename, score, match_summary, skills_matched, skills_missing, red_flags, status } = candidate;

  // Parse JSON strings
  const matched = skills_matched ? JSON.parse(skills_matched) : [];
  const missing = skills_missing ? JSON.parse(skills_missing) : [];
  const flags = red_flags ? JSON.parse(red_flags) : [];

  // Score styling
  let scoreColor = "text-green-500";
  if (score < 5) scoreColor = "text-red-500";
  else if (score < 7.5) scoreColor = "text-yellow-500";

  if (status !== "completed") {
    return (
      <div className="glass-card p-6 animate-pulse">
        <div className="flex justify-between items-center mb-4">
          <div className="h-6 bg-slate-700/50 rounded w-1/3"></div>
          <div className="h-12 w-12 rounded-full bg-slate-700/50"></div>
        </div>
        <div className="space-y-2">
          <div className="h-4 bg-slate-700/50 rounded w-full"></div>
          <div className="h-4 bg-slate-700/50 rounded w-5/6"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="glass-card p-6 border-l-4" style={{ borderLeftColor: score >= 7.5 ? '#22c55e' : score >= 5 ? '#eab308' : '#ef4444' }}>
      <div className="flex justify-between items-start mb-4">
        <div>
          <h3 className="text-lg font-semibold text-white mb-1 truncate max-w-[200px]" title={filename}>
            {filename}
          </h3>
          <p className="text-sm text-slate-400">Processed by AI Worker</p>
        </div>
        <div className="flex flex-col items-center justify-center w-16 h-16 rounded-full bg-slate-800 border-4 border-slate-700 relative">
          <span className={`text-xl font-bold ${scoreColor}`}>{score?.toFixed(1)}</span>
        </div>
      </div>

      <p className="text-sm text-slate-300 mb-6 italic border-l-2 border-brand-500 pl-3">
        "{match_summary}"
      </p>

      <div className="space-y-4">
        {matched.length > 0 && (
          <div>
            <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2 flex items-center gap-1">
              <Check className="w-3 h-3 text-green-500" /> Matched Skills
            </h4>
            <div className="flex flex-wrap gap-2">
              {matched.map((skill, i) => (
                <span key={i} className="px-2.5 py-1 rounded-full bg-green-500/10 text-green-400 border border-green-500/20 text-xs">
                  {skill}
                </span>
              ))}
            </div>
          </div>
        )}

        {missing.length > 0 && (
          <div>
            <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2 flex items-center gap-1">
              <X className="w-3 h-3 text-red-500" /> Missing Skills
            </h4>
            <div className="flex flex-wrap gap-2">
              {missing.map((skill, i) => (
                <span key={i} className="px-2.5 py-1 rounded-full bg-red-500/10 text-red-400 border border-red-500/20 text-xs">
                  {skill}
                </span>
              ))}
            </div>
          </div>
        )}

        {flags.length > 0 && (
          <div className="mt-4 p-3 rounded-lg bg-yellow-500/10 border border-yellow-500/20">
            <h4 className="text-xs font-semibold text-yellow-500 uppercase tracking-wider mb-2 flex items-center gap-1">
              <AlertTriangle className="w-4 h-4" /> Red Flags
            </h4>
            <ul className="list-disc pl-5 text-sm text-yellow-200/80 space-y-1">
              {flags.map((flag, i) => (
                <li key={i}>{flag}</li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
}
