import { useState, useRef, useEffect } from "react";
import { useNavigate } from "react-router";
import {
  Upload,
  FileText,
  X,
  Zap,
  CheckCircle2,
  AlertCircle,
  ChevronRight,
  Plus,
  Loader2,
  Sparkles,
  ArrowRight,
  Wifi,
  WifiOff,
  ServerCrash,
} from "lucide-react";
import { screenResumes, pingBackend, BASE_URL, type ScreeningResult } from "../services/api";

interface UploadedFile {
  id: string;
  name: string;
  size: string;
  rawFile?: File;
  status: "pending" | "processing" | "done" | "error";
  score?: number;
}

const sampleJD = `We are looking for a Senior Full Stack Developer to join our growing engineering team.

Requirements:
• 5+ years of experience in full-stack development
• Proficiency in React, TypeScript, and Node.js
• Strong knowledge of Python for backend services
• Experience with PostgreSQL and database design
• Familiarity with AWS services (EC2, S3, Lambda)
• Docker and containerization experience
• Understanding of CI/CD pipelines

Nice to have:
• GraphQL API design experience
• Kubernetes orchestration
• Experience with microservices architecture
• Open source contributions

Responsibilities:
• Design and build scalable web applications
• Collaborate with cross-functional teams
• Code reviews and mentoring junior developers
• Optimize application performance`;

export function ScreenResumes() {
  const navigate = useNavigate();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [jdText, setJdText] = useState("");
  const [files, setFiles] = useState<UploadedFile[]>([]);
  const [isDragging, setIsDragging] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [isDone, setIsDone] = useState(false);
  const [step, setStep] = useState<1 | 2>(1);
  const [progress, setProgress] = useState(0);
  const [backendStatus, setBackendStatus] = useState<"checking" | "online" | "offline">("checking");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [screeningResults, setScreeningResults] = useState<ScreeningResult[]>([]);
  const [useMockMode, setUseMockMode] = useState(false);

  // Check backend connectivity on mount
  useEffect(() => {
    async function check() {
      const online = await pingBackend();
      setBackendStatus(online ? "online" : "offline");
      if (!online) setUseMockMode(true);
    }
    check();
  }, []);

  const detectedSkills = ["React", "Node.js", "Python", "AWS", "TypeScript", "Docker"].filter((s) =>
    jdText.toLowerCase().includes(s.toLowerCase())
  );

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    addFiles(Array.from(e.dataTransfer.files));
  };

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    addFiles(Array.from(e.target.files || []));
  };

  const addFiles = (newFiles: File[]) => {
    const mapped: UploadedFile[] = newFiles
      .filter((f) => /\.(pdf|doc|docx)$/i.test(f.name))
      .map((f, i) => ({
        id: `f-${Date.now()}-${i}`,
        name: f.name,
        size: `${(f.size / 1024).toFixed(0)} KB`,
        rawFile: f,
        status: "pending",
      }));
    setFiles((prev) => [...prev, ...mapped]);
  };

  const removeFile = (id: string) => {
    setFiles((prev) => prev.filter((f) => f.id !== id));
  };

  // Simulate a mock screening when backend is offline
  const runMockScreening = async () => {
    setIsProcessing(true);
    setProgress(0);
    setErrorMessage(null);

    const mockScores = [94, 88, 82, 74, 91, 65, 77, 58, 85, 70];
    for (let i = 0; i <= 100; i += 4) {
      await new Promise((res) => setTimeout(res, 60));
      setProgress(i);
    }

    const mockResults: ScreeningResult[] = files.map((f, i) => ({
      filename: f.name,
      match_score: mockScores[i % mockScores.length],
      matched_skills: ["Python", "React", "Node.js"].slice(0, 2 + (i % 2)),
      missing_skills: i % 3 === 0 ? ["AWS"] : [],
    }));

    setFiles((prev) =>
      prev.map((f, i) => ({
        ...f,
        status: "done",
        score: mockResults[i]?.match_score,
      }))
    );
    setScreeningResults(mockResults);
    sessionStorage.setItem("screeningResults", JSON.stringify(mockResults));
    setProgress(100);
    setIsProcessing(false);
    setIsDone(true);
  };

  // Real API screening
  const runRealScreening = async () => {
    setIsProcessing(true);
    setProgress(0);
    setErrorMessage(null);

    // Animate progress while waiting
    const progressInterval = setInterval(() => {
      setProgress((p) => (p < 85 ? p + 3 : p));
    }, 200);

    const realFiles = files.map((f) => f.rawFile).filter(Boolean) as File[];

    if (realFiles.length === 0) {
      setErrorMessage("Please upload at least one real PDF, DOC, or DOCX file. Sample placeholders cannot be analyzed by the AI.");
      setIsProcessing(false);
      return;
    }

    try {
      const response = await screenResumes(jdText, realFiles);

      clearInterval(progressInterval);
      setProgress(100);

      // Map results back to files
      const resultMap = new Map(response.results.map((r) => [r.filename, r]));
      setFiles((prev) =>
        prev.map((f) => {
          const result = resultMap.get(f.name);
          return {
            ...f,
            status: result ? "done" : "error",
            score: result?.match_score,
          };
        })
      );

      setScreeningResults(response.results);
      sessionStorage.setItem("screeningResults", JSON.stringify(response.results));
      setIsDone(true);
    } catch (err: any) {
      clearInterval(progressInterval);
      setErrorMessage(err.message || "Screening failed. Check your backend connection.");
      setFiles((prev) => prev.map((f) => ({ ...f, status: "error" })));
    } finally {
      setIsProcessing(false);
    }
  };

  const handleScreen = () => {
    if (useMockMode) {
      runMockScreening();
    } else {
      runRealScreening();
    }
  };

  const loadSampleJD = () => setJdText(sampleJD);

  const loadSampleResumes = async () => {
    setErrorMessage(null);
    try {
      const response = await fetch("/sample_resume.pdf");
      const blob = await response.blob();
      
      const createSampleFile = (name: string) => new File([blob], name, { type: "application/pdf" });

      setFiles([
        { id: "s-1", name: "priya_sharma_resume.pdf", size: "284 KB", status: "pending", rawFile: createSampleFile("priya_sharma_resume.pdf") },
        { id: "s-2", name: "marcus_johnson_resume.pdf", size: "312 KB", status: "pending", rawFile: createSampleFile("marcus_johnson_resume.pdf") },
        { id: "s-3", name: "aisha_patel_resume.pdf", size: "198 KB", status: "pending", rawFile: createSampleFile("aisha_patel_resume.pdf") },
        { id: "s-4", name: "david_chen_resume.pdf", size: "256 KB", status: "pending", rawFile: createSampleFile("david_chen_resume.pdf") },
        { id: "s-5", name: "sofia_rodriguez_resume.pdf", size: "344 KB", status: "pending", rawFile: createSampleFile("sofia_rodriguez_resume.pdf") },
      ]);
    } catch (err) {
      console.error("Failed to load sample resumes:", err);
      // Fallback to placeholders if fetch fails
      setFiles([
        { id: "s-1", name: "priya_sharma_resume.pdf", size: "284 KB", status: "pending" },
        { id: "s-2", name: "marcus_johnson_resume.pdf", size: "312 KB", status: "pending" },
      ]);
    }
  };

  return (
    <div className="p-4 lg:p-6">
      {/* Header */}
      <div className="mb-5">
        <h1 className="text-gray-900" style={{ fontWeight: 700, fontSize: "1.375rem" }}>
          Screen Resumes
        </h1>
        <p className="text-gray-500 text-sm mt-0.5">
          Upload a job description and resumes to get AI-powered match scores
        </p>
      </div>

      {/* Backend status banner */}
      <div
        className={`flex items-center gap-3 px-4 py-3 rounded-xl mb-5 text-sm border ${
          backendStatus === "online"
            ? "bg-emerald-50 border-emerald-200 text-emerald-700"
            : backendStatus === "offline"
            ? "bg-amber-50 border-amber-200 text-amber-700"
            : "bg-gray-50 border-gray-200 text-gray-500"
        }`}
      >
        {backendStatus === "online" ? (
          <Wifi size={15} className="flex-shrink-0" />
        ) : backendStatus === "offline" ? (
          <WifiOff size={15} className="flex-shrink-0" />
        ) : (
          <Loader2 size={15} className="animate-spin flex-shrink-0" />
        )}
        <div className="flex-1 min-w-0">
          {backendStatus === "online" && (
            <span style={{ fontWeight: 500 }}>
              Backend connected — <span className="opacity-70">{BASE_URL}</span>
            </span>
          )}
          {backendStatus === "offline" && (
            <span style={{ fontWeight: 500 }}>
              Backend not detected at <span className="font-mono opacity-80">{BASE_URL}</span> — running in{" "}
              <span className="underline cursor-pointer" onClick={() => { setUseMockMode(true); }}>
                demo mode
              </span>
            </span>
          )}
          {backendStatus === "checking" && <span>Connecting to backend...</span>}
        </div>
        {backendStatus === "offline" && (
          <div className="flex items-center gap-2 flex-shrink-0">
            <button
              onClick={async () => {
                setBackendStatus("checking");
                const ok = await pingBackend();
                setBackendStatus(ok ? "online" : "offline");
                setUseMockMode(!ok);
              }}
              className="text-xs px-2.5 py-1 rounded-lg bg-amber-100 hover:bg-amber-200 transition-colors"
              style={{ fontWeight: 500 }}
            >
              Retry
            </button>
          </div>
        )}
      </div>

      {/* Setup instructions for offline mode */}
      {backendStatus === "offline" && (
        <div className="bg-gray-900 rounded-xl p-4 mb-5 text-xs font-mono text-gray-300 space-y-1.5">
          <p className="text-violet-400" style={{ fontWeight: 600 }}>
            # Start your Resume Screener backend:
          </p>
          <p>$ git clone https://github.com/Akilanan/Resume-Screener.git</p>
          <p>$ cd Resume-Screener</p>
          <p>$ pip install -r requirements.txt</p>
          <p>$ python app.py</p>
          <p className="text-gray-500 mt-2"># Then set VITE_API_URL=http://localhost:5000 in .env</p>
        </div>
      )}

      {/* Steps */}
      <div className="flex items-center gap-3 mb-5">
        {[
          { num: 1, label: "Job Description" },
          { num: 2, label: "Upload Resumes" },
        ].map(({ num, label }, i) => (
          <div key={num} className="flex items-center gap-2">
            <div
              className={`flex items-center justify-center w-7 h-7 rounded-full text-xs transition-all ${
                step >= num ? "bg-violet-600 text-white" : "bg-gray-100 text-gray-400"
              }`}
              style={{ fontWeight: 700 }}
            >
              {step > num ? <CheckCircle2 size={14} /> : num}
            </div>
            <span
              className={`text-sm ${step >= num ? "text-gray-700" : "text-gray-400"}`}
              style={{ fontWeight: step >= num ? 500 : 400 }}
            >
              {label}
            </span>
            {i < 1 && <ChevronRight size={14} className="text-gray-300 ml-1" />}
          </div>
        ))}
        {useMockMode && backendStatus === "offline" && (
          <span className="ml-auto text-xs px-2.5 py-1 rounded-full bg-amber-100 text-amber-700 border border-amber-200" style={{ fontWeight: 500 }}>
            Demo Mode
          </span>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        {/* Job Description */}
        <div className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
          <div className="flex items-center justify-between px-5 py-4 border-b border-gray-50">
            <div>
              <h2 className="text-gray-900 text-sm" style={{ fontWeight: 600 }}>
                Job Description
              </h2>
              <p className="text-gray-400 text-xs mt-0.5">Paste the job requirements</p>
            </div>
            <button
              onClick={loadSampleJD}
              className="text-xs text-violet-600 hover:text-violet-700 px-3 py-1.5 rounded-lg bg-violet-50 hover:bg-violet-100 transition-colors"
              style={{ fontWeight: 500 }}
            >
              Load Sample
            </button>
          </div>

          <div className="p-4">
            {/* Auto-detected skills */}
            <div className="flex flex-wrap gap-2 mb-3">
              {["React", "Node.js", "Python", "AWS", "TypeScript", "Docker"].map((tag) => (
                <span
                  key={tag}
                  className={`px-2.5 py-1 rounded-full text-xs transition-all ${
                    detectedSkills.includes(tag)
                      ? "bg-violet-100 text-violet-700 border border-violet-200"
                      : "bg-gray-100 text-gray-400"
                  }`}
                  style={{ fontWeight: 500 }}
                >
                  {tag}
                </span>
              ))}
              {detectedSkills.length > 0 && (
                <span className="text-xs text-gray-400 flex items-center gap-1">
                  <Sparkles size={11} /> {detectedSkills.length} skills detected
                </span>
              )}
            </div>

            <textarea
              value={jdText}
              onChange={(e) => {
                setJdText(e.target.value);
                if (e.target.value.trim() && step === 1) setStep(2);
              }}
              placeholder={`Paste your job description here...\n\nInclude:\n• Required skills and technologies\n• Years of experience\n• Responsibilities\n• Education requirements`}
              className="w-full h-80 text-sm text-gray-700 placeholder-gray-300 resize-none outline-none leading-relaxed"
              style={{ fontFamily: "inherit" }}
            />
          </div>

          <div className="px-5 py-3 bg-gray-50 border-t border-gray-100 flex items-center gap-2">
            <div className={`w-2 h-2 rounded-full ${jdText.trim() ? "bg-emerald-400" : "bg-gray-300"}`} />
            <span className="text-xs text-gray-500">
              {jdText.trim()
                ? `${jdText.trim().split(/\s+/).length} words · ${detectedSkills.length} skills detected`
                : "Waiting for job description"}
            </span>
          </div>
        </div>

        {/* Resume Upload */}
        <div className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden flex flex-col">
          <div className="flex items-center justify-between px-5 py-4 border-b border-gray-50">
            <div>
              <h2 className="text-gray-900 text-sm" style={{ fontWeight: 600 }}>
                Upload Resumes
              </h2>
              <p className="text-gray-400 text-xs mt-0.5">PDF, DOC, DOCX supported</p>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={loadSampleResumes}
                className="text-xs text-violet-600 hover:text-violet-700 px-3 py-1.5 rounded-lg bg-violet-50 hover:bg-violet-100 transition-colors"
                style={{ fontWeight: 500 }}
              >
                Load Sample
              </button>
              <button
                onClick={() => fileInputRef.current?.click()}
                className="flex items-center gap-1 text-xs text-white bg-violet-600 hover:bg-violet-700 px-3 py-1.5 rounded-lg transition-colors"
                style={{ fontWeight: 500 }}
              >
                <Plus size={13} /> Add Files
              </button>
            </div>
          </div>

          <input
            ref={fileInputRef}
            type="file"
            multiple
            accept=".pdf,.doc,.docx"
            className="hidden"
            onChange={handleFileInput}
          />

          {/* Drop zone */}
          <div
            onDrop={handleDrop}
            onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
            onDragLeave={() => setIsDragging(false)}
            onClick={() => files.length === 0 && fileInputRef.current?.click()}
            className={`mx-4 mt-4 rounded-xl border-2 border-dashed transition-all cursor-pointer
              ${isDragging ? "border-violet-400 bg-violet-50" : "border-gray-200 hover:border-violet-300 hover:bg-gray-50"}
              ${files.length > 0 ? "py-3" : "py-8"}`}
          >
            {files.length === 0 ? (
              <div className="text-center">
                <div className="w-12 h-12 rounded-2xl bg-violet-50 flex items-center justify-center mx-auto mb-3">
                  <Upload size={22} className="text-violet-400" />
                </div>
                <p className="text-gray-600 text-sm" style={{ fontWeight: 500 }}>
                  Drop resumes here or click to browse
                </p>
                <p className="text-gray-400 text-xs mt-1">PDF, DOC, DOCX · Max 10MB each</p>
              </div>
            ) : (
              <p className="text-center text-violet-600 text-xs py-1" style={{ fontWeight: 500 }}>
                + Drop more files here
              </p>
            )}
          </div>

          {/* File list */}
          <div className="flex-1 px-4 mt-3 space-y-2 overflow-y-auto" style={{ maxHeight: "240px" }}>
            {files.map((file) => (
              <div
                key={file.id}
                className={`flex items-center gap-3 p-3 rounded-xl border transition-colors ${
                  file.status === "error"
                    ? "bg-red-50 border-red-100"
                    : file.status === "done"
                    ? "bg-gray-50 border-gray-100"
                    : "bg-gray-50 border-gray-100"
                }`}
              >
                <div className="w-8 h-8 rounded-lg bg-red-50 flex items-center justify-center flex-shrink-0">
                  <FileText size={15} className="text-red-400" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-gray-700 text-xs truncate" style={{ fontWeight: 500 }}>
                    {file.name}
                  </p>
                  <div className="flex items-center gap-2 mt-0.5">
                    <span className="text-gray-400 text-xs">{file.size}</span>
                    {file.status === "done" && file.score !== undefined && (
                      <span
                        className={`text-xs px-2 py-0.5 rounded-full ${
                          file.score >= 85
                            ? "bg-emerald-100 text-emerald-700"
                            : file.score >= 70
                            ? "bg-amber-100 text-amber-700"
                            : "bg-red-100 text-red-600"
                        }`}
                        style={{ fontWeight: 600 }}
                      >
                        {file.score}% match
                      </span>
                    )}
                    {file.status === "error" && (
                      <span className="text-xs text-red-500">processing failed</span>
                    )}
                  </div>
                </div>
                {!isProcessing && (
                  <button
                    onClick={() => removeFile(file.id)}
                    className="p-1 rounded-lg hover:bg-gray-200 text-gray-400 hover:text-gray-600 transition-colors"
                  >
                    <X size={13} />
                  </button>
                )}
                {file.status === "done" && (
                  <CheckCircle2 size={15} className="text-emerald-500 flex-shrink-0" />
                )}
                {file.status === "processing" && (
                  <Loader2 size={15} className="text-violet-500 animate-spin flex-shrink-0" />
                )}
              </div>
            ))}
          </div>

          {/* Progress */}
          {isProcessing && (
            <div className="px-4 mt-3">
              <div className="flex items-center justify-between mb-1.5">
                <span className="text-xs text-gray-500">
                  {useMockMode ? "Running demo analysis..." : "Sending to backend..."}
                </span>
                <span className="text-xs text-violet-600" style={{ fontWeight: 600 }}>{progress}%</span>
              </div>
              <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-violet-500 to-purple-500 rounded-full transition-all duration-300"
                  style={{ width: `${progress}%` }}
                />
              </div>
              <p className="text-xs text-gray-400 mt-1.5">
                Extracting skills · Matching requirements · Calculating scores
              </p>
            </div>
          )}

          {/* Error */}
          {errorMessage && (
            <div className="mx-4 mt-3 flex items-start gap-2 p-3 rounded-xl bg-red-50 border border-red-100">
              <ServerCrash size={14} className="text-red-500 flex-shrink-0 mt-0.5" />
              <div>
                <p className="text-red-700 text-xs" style={{ fontWeight: 600 }}>Backend Error</p>
                <p className="text-red-500 text-xs mt-0.5">{errorMessage}</p>
                <button
                  onClick={() => { setUseMockMode(true); setErrorMessage(null); setIsDone(false); setFiles(f => f.map(x => ({...x, status: "pending", score: undefined}))); }}
                  className="text-xs text-red-600 underline mt-1"
                >
                  Switch to demo mode
                </button>
              </div>
            </div>
          )}

          {/* CTA */}
          <div className="p-4 mt-2">
            {!isDone ? (
              <button
                onClick={handleScreen}
                disabled={!jdText.trim() || files.length === 0 || isProcessing}
                className={`w-full flex items-center justify-center gap-2 py-3 rounded-xl text-sm transition-all ${
                  !jdText.trim() || files.length === 0 || isProcessing
                    ? "bg-gray-100 text-gray-400 cursor-not-allowed"
                    : "bg-gradient-to-r from-violet-600 to-purple-600 text-white shadow-lg shadow-violet-200 hover:shadow-violet-300 hover:from-violet-700 hover:to-purple-700"
                }`}
                style={{ fontWeight: 600 }}
              >
                {isProcessing ? (
                  <>
                    <Loader2 size={16} className="animate-spin" />
                    Analyzing {files.length} resume{files.length !== 1 ? "s" : ""}...
                  </>
                ) : (
                  <>
                    <Zap size={16} />
                    Screen {files.length > 0 ? `${files.length} ` : ""}Resume{files.length !== 1 ? "s" : ""} with AI
                  </>
                )}
              </button>
            ) : (
              <div className="space-y-2">
                <div className="flex items-center gap-2 p-3 rounded-xl bg-emerald-50 border border-emerald-100">
                  <CheckCircle2 size={16} className="text-emerald-600 flex-shrink-0" />
                  <p className="text-emerald-700 text-sm" style={{ fontWeight: 500 }}>
                    Done! {files.length} resume{files.length !== 1 ? "s" : ""} analyzed.
                    {useMockMode && <span className="text-emerald-500 ml-1">(demo scores)</span>}
                  </p>
                </div>
                <button
                  onClick={() => navigate("/results")}
                  className="w-full flex items-center justify-center gap-2 py-3 rounded-xl text-sm bg-gradient-to-r from-violet-600 to-purple-600 text-white shadow-lg shadow-violet-200 hover:from-violet-700 hover:to-purple-700 transition-all"
                  style={{ fontWeight: 600 }}
                >
                  View Ranked Results <ArrowRight size={15} />
                </button>
              </div>
            )}

            {!jdText.trim() && !isProcessing && (
              <p className="text-center text-xs text-gray-400 mt-2 flex items-center justify-center gap-1">
                <AlertCircle size={11} /> Add a job description to start screening
              </p>
            )}
          </div>
        </div>
      </div>

      {/* Tips */}
      <div className="mt-5 grid grid-cols-1 sm:grid-cols-3 gap-4">
        {[
          {
            icon: "📋",
            title: "Detailed JD = Better Results",
            desc: "Include specific skills, experience levels, and requirements for more accurate scoring",
          },
          {
            icon: "📄",
            title: "Batch Upload",
            desc: "Upload up to 100 resumes at once. The AI processes them all in under 3 minutes",
          },
          {
            icon: "🎯",
            title: "Smart NLP Matching",
            desc: "The backend uses NLP to understand context and synonyms — not just keyword matching",
          },
        ].map((tip) => (
          <div key={tip.title} className="bg-white rounded-xl border border-gray-100 p-4 flex gap-3">
            <span className="text-xl flex-shrink-0">{tip.icon}</span>
            <div>
              <p className="text-gray-700 text-sm" style={{ fontWeight: 600 }}>{tip.title}</p>
              <p className="text-gray-400 text-xs mt-1 leading-relaxed">{tip.desc}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
