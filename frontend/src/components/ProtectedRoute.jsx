import { Navigate } from "react-router-dom";
import { isAuthenticated, getUserRole } from "../services/auth";

export default function ProtectedRoute({ children, roleRequired }) {
  if (!isAuthenticated()) {
    return <Navigate to="/login" replace />;
  }

  if (roleRequired && getUserRole() !== roleRequired) {
    return <Navigate to="/dashboard" replace />;
  }

  return children;
}
