import MockAdapter from 'axios-mock-adapter';
import api from './api';

const mock = new MockAdapter(api, { delayResponse: 800 });

// === Auth Mocks ===
mock.onPost('/auth/login').reply(200, {
  message: "OTP sent to your email",
  mfa_required: true
});

mock.onPost('/auth/verify-otp').reply(200, {
  access_token: "mock-access-token",
  refresh_token: "mock-refresh-token",
  token_type: "bearer",
  role: "admin" // switch to 'hr' to test non-admin role
});

mock.onPost('/auth/refresh').reply(200, {
  access_token: "mock-new-access-token",
  token_type: "bearer"
});

// === Jobs Mocks ===
let mockJobs = [
  {
    id: "job-1234",
    title: "Senior React Developer",
    description: "Looking for an expert React developer with deep understanding of hooks, context, and modern UI.",
    status: "open",
    created_at: new Date().toISOString()
  }
];

mock.onGet('/jobs/').reply(() => {
  return [200, mockJobs];
});

mock.onPost('/jobs/').reply((config) => {
  const data = JSON.parse(config.data);
  const newJob = {
    id: `job-${Math.floor(Math.random() * 10000)}`,
    title: data.title,
    description: data.description,
    status: "open",
    created_at: new Date().toISOString()
  };
  mockJobs.push(newJob);
  return [200, newJob];
});

// === Resumes Mocks ===
let mockCandidates = [
  {
    id: "res-1",
    filename: "Alex_Smith_Resume.pdf",
    status: "completed",
    score: 8.9,
    match_summary: "Strong react candidate with deep understanding of the exact tech stack.",
    skills_matched: JSON.stringify(["React", "REST API", "TailwindCSS"]),
    skills_missing: JSON.stringify(["GraphQL"]),
    red_flags: JSON.stringify([]),
    uploaded_at: new Date().toISOString()
  },
  {
    id: "res-2",
    filename: "Jane_Doe_CV.pdf",
    status: "completed",
    score: 4.2,
    match_summary: "Lacks core frontend experience mentioned in JD.",
    skills_matched: JSON.stringify(["Python", "SQL"]),
    skills_missing: JSON.stringify(["React", "JavaScript"]),
    red_flags: JSON.stringify(["Frequent job hopping observed"]),
    uploaded_at: new Date().toISOString()
  }
];

mock.onGet(/\/resumes\/results\/.+/).reply(() => {
  return [200, mockCandidates];
});

mock.onPost(/\/resumes\/upload\/.+/).reply(() => {
  const newCandidate = {
    id: `res-${Math.random()}`,
    filename: "New_Uploaded_Resume.pdf",
    status: "completed",
    score: 7.5,
    match_summary: "Good potential fit. AI worker processed this instantly.",
    skills_matched: JSON.stringify(["React", "JavaScript"]),
    skills_missing: JSON.stringify(["Docker"]),
    red_flags: JSON.stringify([]),
    uploaded_at: new Date().toISOString()
  };
  mockCandidates.push(newCandidate);
  return [200, { uploaded: 1, resumes: [newCandidate] }];
});

// === Admin Mocks ===
mock.onGet('/admin/stats').reply(200, {
  total_users: 12,
  total_jobs: 5,
  total_resumes: 142,
  completed_resumes: 142
});

mock.onGet('/admin/users').reply(200, [
  {
    id: "usr-admin-1",
    email: "admin@talentai.com",
    role: "admin",
    is_active: true,
    mfa_enabled: true,
    created_at: new Date(Date.now() - 1000000000).toISOString()
  },
  {
    id: "usr-hr-2",
    email: "sarah.hr@talentai.com",
    role: "hr",
    is_active: true,
    mfa_enabled: false,
    created_at: new Date(Date.now() - 500000000).toISOString()
  }
]);

export default mock;
