import { createBrowserRouter, Navigate } from "react-router";
import { Layout } from "./components/Layout";
import { Dashboard } from "./components/Dashboard";
import { ScreenResumes } from "./components/ScreenResumes";
import { Results } from "./components/Results";
import { CandidateDetail } from "./components/CandidateDetail";
import { JobDescriptions } from "./components/JobDescriptions";
import { Login } from "./components/Login";

const ProtectedRoute = ({ children }: { children: React.ReactNode }) => {
  const token = localStorage.getItem("access_token");
  if (!token) return <Navigate to="/login" replace />;
  return <>{children}</>;
};

export const router = createBrowserRouter([
  {
    path: "/login",
    Component: Login,
  },
  {
    path: "/",
    element: (
      <ProtectedRoute>
        <Layout />
      </ProtectedRoute>
    ),
    children: [
      { index: true, Component: Dashboard },
      { path: "screen", Component: ScreenResumes },
      { path: "results", Component: Results },
      { path: "results/:id", Component: CandidateDetail },
      { path: "jobs", Component: JobDescriptions },
    ],
  },
]);
