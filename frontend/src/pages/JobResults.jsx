import { useState, useCallback, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useDropzone } from "react-dropzone";
import api from "../services/api";
import Navbar from "../components/Navbar";
import CandidateCard from "../components/CandidateCard";
import { UploadCloud, ArrowLeft, RefreshCw, AlertCircle } from "lucide-react";

export default function JobResults() {
  const { jobId } = useParams();
  const navigate = useNavigate();
  const [candidates, setCandidates] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [polling, setPolling] = useState(false);
  
  const fetchResults = async () => {
    try {
      const res = await api.get(`/resumes/results/${jobId}`);
      setCandidates(res.data);
      
      // If there are pending resumes, keep polling
      const hasPending = res.data.some(c => c.status !== 'completed' && c.status !== 'failed');
      return hasPending;
    } catch (err) {
      console.error(err);
      return false;
    }
  };

  // Poll for updates if needed
  useEffect(() => {
    let intervalId;
    if (polling) {
      intervalId = setInterval(async () => {
        const keepsPolling = await fetchResults();
        if (!keepsPolling) setPolling(false);
      }, 3000);
    }
    return () => clearInterval(intervalId);
  }, [polling, jobId]);

  // Initial fetch
  useEffect(() => {
    fetchResults().then(hasPending => {
      if (hasPending) setPolling(true);
    });
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [jobId]);

  const onDrop = useCallback(async (acceptedFiles) => {
    if (acceptedFiles.length === 0) return;
    
    setUploading(true);
    const formData = new FormData();
    acceptedFiles.forEach(file => {
      formData.append("files", file);
    });

    try {
      await api.post(`/resumes/upload/${jobId}`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      // Start polling after successful upload
      setPolling(true);
      fetchResults();
    } catch (err) {
      console.error(err);
      alert("Upload failed. Ensure you're uploading PDFs.");
    } finally {
      setUploading(false);
    }
  }, [jobId]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({ 
    onDrop,
    accept: { 'application/pdf': ['.pdf'] }
  });

  return (
    <div className="min-h-screen bg-bg-dark flex flex-col">
      <Navbar />

      <main className="flex-1 p-8 max-w-7xl mx-auto w-full">
        <button 
          onClick={() => navigate("/dashboard")}
          className="flex items-center text-slate-400 hover:text-white mb-6 transition-colors"
        >
          <ArrowLeft className="w-4 h-4 mr-2" /> Back to Dashboard
        </button>

        <div className="flex justify-between items-center mb-8">
          <h1 className="text-3xl font-bold text-white">Candidate Screening</h1>
          {polling && (
            <div className="flex items-center text-brand-400 bg-brand-500/10 px-4 py-2 rounded-full text-sm font-medium border border-brand-500/20">
              <RefreshCw className="w-4 h-4 mr-2 animate-spin" /> 
              AI Workers processing...
            </div>
          )}
        </div>

        {/* Drag and Drop Area */}
        <div 
          {...getRootProps()} 
          className={`mb-10 p-12 border-2 border-dashed rounded-2xl text-center transition-all cursor-pointer
            ${isDragActive ? 'border-brand-500 bg-brand-500/5' : 'border-slate-700 hover:border-brand-500/50 hover:bg-slate-800/30 bg-slate-900/50'}`}
        >
          <input {...getInputProps()} />
          <UploadCloud className={`w-16 h-16 mx-auto mb-4 ${isDragActive ? 'text-brand-400' : 'text-slate-500'}`} />
          <h3 className="text-xl font-medium text-white mb-2">Drop resumes here to analyze</h3>
          <p className="text-slate-400 mb-6">Supports PDF files. You can upload multiple resumes at once.</p>
          <button 
            disabled={uploading}
            className="px-6 py-2 bg-white text-slate-900 font-medium rounded-lg hover:bg-slate-200 transition-colors disabled:opacity-50"
          >
            {uploading ? 'Uploading...' : 'Browse Files'}
          </button>
        </div>

        {/* Results grid */}
        <div className="space-y-6">
          <h2 className="text-xl font-semibold text-white flex items-center border-b border-slate-800 pb-2">
            Ranked Candidates
            <span className="ml-3 bg-slate-800 text-slate-300 px-3 py-1 rounded-full text-sm">
              {candidates.length}
            </span>
          </h2>
          
          {candidates.length === 0 ? (
            <div className="text-center py-10 text-slate-500 flex flex-col items-center">
              <AlertCircle className="w-10 h-10 mb-3 opacity-50" />
              <p>No candidates uploaded yet.</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {candidates.map(candidate => (
                <CandidateCard key={candidate.id} candidate={candidate} />
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
