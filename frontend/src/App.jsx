import { BrowserRouter as Router, Routes, Route, Navigate } from "react-router-dom";
import Login from "./pages/Login";
import MFAVerify from "./pages/MFAVerify";
import HRDashboard from "./pages/HRDashboard";
import AdminPanel from "./pages/AdminPanel";
import JobResults from "./pages/JobResults";
import ProtectedRoute from "./components/ProtectedRoute";

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/mfa" element={<MFAVerify />} />
        
        <Route 
          path="/dashboard" 
          element={
            <ProtectedRoute>
              <HRDashboard />
            </ProtectedRoute>
          } 
        />
        
        <Route 
          path="/jobs/:jobId" 
          element={
            <ProtectedRoute>
              <JobResults />
            </ProtectedRoute>
          } 
        />

        <Route 
          path="/admin" 
          element={
            <ProtectedRoute roleRequired="admin">
              <AdminPanel />
            </ProtectedRoute>
          } 
        />

        {/* Redirect root to dashboard */}
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </Router>
  );
}

export default App;
