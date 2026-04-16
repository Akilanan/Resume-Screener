export interface Candidate {
  id: string;
  name: string;
  email: string;
  phone: string;
  location: string;
  experience: number; // years
  education: string;
  currentRole: string;
  matchScore: number; // 0-100
  skillsMatched: string[];
  skillsMissing: string[];
  summary: string;
  resumeFile: string;
  appliedFor: string;
  screened: string; // date
  status: "shortlisted" | "reviewing" | "rejected" | "pending";
  keyHighlights: string[];
}

export interface JobDescription {
  id: string;
  title: string;
  department: string;
  location: string;
  type: string;
  description: string;
  requiredSkills: string[];
  niceToHave: string[];
  experience: string;
  education: string;
  createdAt: string;
  candidatesScreened: number;
  status: "active" | "closed" | "draft";
}

export const jobDescriptions: JobDescription[] = [
  {
    id: "jd-001",
    title: "Senior Full Stack Developer",
    department: "Engineering",
    location: "Remote",
    type: "Full-time",
    description:
      "We are looking for a Senior Full Stack Developer to join our growing team. You will work on building scalable web applications using modern technologies.",
    requiredSkills: ["React", "Node.js", "Python", "PostgreSQL", "AWS", "Docker", "TypeScript"],
    niceToHave: ["GraphQL", "Kubernetes", "Redis", "Machine Learning"],
    experience: "5+ years",
    education: "Bachelor's in Computer Science or related field",
    createdAt: "2026-04-01",
    candidatesScreened: 24,
    status: "active",
  },
  {
    id: "jd-002",
    title: "Machine Learning Engineer",
    department: "AI/ML",
    location: "San Francisco, CA",
    type: "Full-time",
    description:
      "Join our AI team to build cutting-edge machine learning models and deploy them at scale. You'll work with large datasets and state-of-the-art algorithms.",
    requiredSkills: ["Python", "TensorFlow", "PyTorch", "Scikit-learn", "NLP", "SQL", "Git"],
    niceToHave: ["MLflow", "Kubeflow", "Spark", "Scala"],
    experience: "3+ years",
    education: "Master's or PhD in ML, Statistics, or related field",
    createdAt: "2026-04-05",
    candidatesScreened: 18,
    status: "active",
  },
  {
    id: "jd-003",
    title: "Product Designer",
    department: "Design",
    location: "New York, NY",
    type: "Full-time",
    description:
      "We're seeking a talented Product Designer to help shape the future of our user experience. You'll collaborate with engineers and product managers.",
    requiredSkills: ["Figma", "UX Research", "Prototyping", "Design Systems", "User Testing"],
    niceToHave: ["Motion Design", "HTML/CSS", "Framer"],
    experience: "3+ years",
    education: "Bachelor's in Design, HCI, or related field",
    createdAt: "2026-04-08",
    candidatesScreened: 12,
    status: "active",
  },
  {
    id: "jd-004",
    title: "DevOps Engineer",
    department: "Infrastructure",
    location: "Austin, TX",
    type: "Full-time",
    description:
      "Looking for a DevOps Engineer to manage our cloud infrastructure and CI/CD pipelines. You'll ensure high availability and reliability of our systems.",
    requiredSkills: ["Kubernetes", "Docker", "AWS", "Terraform", "CI/CD", "Linux", "Python"],
    niceToHave: ["Go", "Prometheus", "Grafana", "Ansible"],
    experience: "4+ years",
    education: "Bachelor's in Computer Science or related field",
    createdAt: "2026-03-20",
    candidatesScreened: 9,
    status: "closed",
  },
];

export const candidates: Candidate[] = [
  {
    id: "c-001",
    name: "Priya Sharma",
    email: "priya.sharma@email.com",
    phone: "+1 (415) 555-0123",
    location: "San Francisco, CA",
    experience: 6,
    education: "M.S. Computer Science, Stanford University",
    currentRole: "Senior Software Engineer at Google",
    matchScore: 94,
    skillsMatched: ["React", "Node.js", "Python", "PostgreSQL", "AWS", "Docker", "TypeScript"],
    skillsMissing: ["GraphQL"],
    summary:
      "Highly experienced full-stack developer with 6 years of expertise in building scalable web applications. Strong background in cloud infrastructure and modern JavaScript frameworks.",
    resumeFile: "priya_sharma_resume.pdf",
    appliedFor: "jd-001",
    screened: "2026-04-10",
    status: "shortlisted",
    keyHighlights: [
      "Led a team of 8 engineers at Google",
      "Reduced API latency by 40% using caching strategies",
      "Built real-time dashboard serving 1M+ daily users",
      "Open source contributor with 2K+ GitHub stars",
    ],
  },
  {
    id: "c-002",
    name: "Marcus Johnson",
    email: "marcus.j@email.com",
    phone: "+1 (312) 555-0456",
    location: "Chicago, IL",
    experience: 7,
    education: "B.S. Computer Science, University of Illinois",
    currentRole: "Staff Engineer at Stripe",
    matchScore: 88,
    skillsMatched: ["React", "TypeScript", "Node.js", "AWS", "Docker", "PostgreSQL"],
    skillsMissing: ["Python", "Kubernetes"],
    summary:
      "Staff Engineer with deep expertise in distributed systems and payment infrastructure. Proven track record in leading complex technical projects.",
    resumeFile: "marcus_johnson_resume.pdf",
    appliedFor: "jd-001",
    screened: "2026-04-11",
    status: "shortlisted",
    keyHighlights: [
      "Architected payment processing system handling $2B+ transactions",
      "Mentored 15+ junior engineers",
      "Patent holder in distributed systems",
      "Published author in IEEE conferences",
    ],
  },
  {
    id: "c-003",
    name: "Aisha Patel",
    email: "aisha.patel@email.com",
    phone: "+1 (650) 555-0789",
    location: "Mountain View, CA",
    experience: 4,
    education: "Ph.D. Machine Learning, MIT",
    currentRole: "ML Research Engineer at Meta",
    matchScore: 96,
    skillsMatched: ["Python", "TensorFlow", "PyTorch", "Scikit-learn", "NLP", "SQL", "Git"],
    skillsMissing: [],
    summary:
      "PhD-level ML researcher with expertise in NLP and computer vision. Published multiple papers in top-tier conferences and has hands-on experience deploying production ML systems.",
    resumeFile: "aisha_patel_resume.pdf",
    appliedFor: "jd-002",
    screened: "2026-04-09",
    status: "shortlisted",
    keyHighlights: [
      "3 publications in NeurIPS and ICML",
      "Built LLM fine-tuning pipeline at Meta",
      "Expertise in RAG and vector databases",
      "Kaggle Grandmaster",
    ],
  },
  {
    id: "c-004",
    name: "David Chen",
    email: "david.chen@email.com",
    phone: "+1 (206) 555-0321",
    location: "Seattle, WA",
    experience: 5,
    education: "M.S. Statistics, University of Washington",
    currentRole: "Senior Data Scientist at Amazon",
    matchScore: 82,
    skillsMatched: ["Python", "Scikit-learn", "SQL", "Git", "TensorFlow"],
    skillsMissing: ["PyTorch", "NLP", "MLflow"],
    summary:
      "Data scientist with strong statistical background and experience in building recommendation systems at scale. Transitioned from academia to industry 5 years ago.",
    resumeFile: "david_chen_resume.pdf",
    appliedFor: "jd-002",
    screened: "2026-04-10",
    status: "reviewing",
    keyHighlights: [
      "Built Amazon's product recommendation engine",
      "A/B tested 50+ features impacting 100M+ customers",
      "Expert in causal inference and experimentation",
      "Speaker at PyData conferences",
    ],
  },
  {
    id: "c-005",
    name: "Sofia Rodriguez",
    email: "sofia.r@email.com",
    phone: "+1 (737) 555-0654",
    location: "Austin, TX",
    experience: 3,
    education: "B.F.A. Graphic Design, UT Austin",
    currentRole: "Product Designer at Figma",
    matchScore: 91,
    skillsMatched: ["Figma", "UX Research", "Prototyping", "Design Systems", "User Testing"],
    skillsMissing: ["Motion Design"],
    summary:
      "Passionate product designer with a strong portfolio spanning fintech, healthcare, and SaaS products. Known for user-centered design thinking and excellent collaboration skills.",
    resumeFile: "sofia_rodriguez_resume.pdf",
    appliedFor: "jd-003",
    screened: "2026-04-12",
    status: "shortlisted",
    keyHighlights: [
      "Designed Figma's component library used by 4M+ users",
      "Led redesign that increased user retention by 35%",
      "Speaker at Config 2025",
      "Accessibility advocate and WCAG expert",
    ],
  },
  {
    id: "c-006",
    name: "James Okafor",
    email: "james.ok@email.com",
    phone: "+1 (929) 555-0987",
    location: "New York, NY",
    experience: 2,
    education: "B.S. Human-Computer Interaction, Carnegie Mellon",
    currentRole: "UX Designer at Spotify",
    matchScore: 74,
    skillsMatched: ["Figma", "Prototyping", "User Testing", "UX Research"],
    skillsMissing: ["Design Systems", "Motion Design", "HTML/CSS"],
    summary:
      "Creative UX designer with a focus on music and entertainment products. Strong user research skills and ability to translate insights into intuitive interfaces.",
    resumeFile: "james_okafor_resume.pdf",
    appliedFor: "jd-003",
    screened: "2026-04-12",
    status: "reviewing",
    keyHighlights: [
      "Redesigned Spotify's podcast discovery flow",
      "Conducted 100+ user interviews",
      "Certified in UX research methods",
    ],
  },
  {
    id: "c-007",
    name: "Elena Volkov",
    email: "elena.v@email.com",
    phone: "+1 (510) 555-0147",
    location: "Oakland, CA",
    experience: 2,
    education: "B.S. Information Technology, UC Berkeley",
    currentRole: "Junior Developer at Startup",
    matchScore: 52,
    skillsMatched: ["React", "Python", "Node.js"],
    skillsMissing: ["AWS", "Docker", "TypeScript", "PostgreSQL", "Kubernetes"],
    summary:
      "Enthusiastic junior developer eager to grow. Has some practical experience with web development and is quick to learn new technologies.",
    resumeFile: "elena_volkov_resume.pdf",
    appliedFor: "jd-001",
    screened: "2026-04-13",
    status: "rejected",
    keyHighlights: [
      "Built 3 personal projects on GitHub",
      "Completed AWS Cloud Practitioner certification",
      "Active in local coding meetups",
    ],
  },
  {
    id: "c-008",
    name: "Raj Krishnamurthy",
    email: "raj.k@email.com",
    phone: "+1 (408) 555-0258",
    location: "San Jose, CA",
    experience: 8,
    education: "M.S. Computer Science, IIT Bombay",
    currentRole: "Principal Engineer at Cisco",
    matchScore: 85,
    skillsMatched: ["Python", "Docker", "AWS", "Linux", "CI/CD", "Kubernetes"],
    skillsMissing: ["Terraform", "Go"],
    summary:
      "Senior infrastructure engineer with 8 years of experience managing large-scale distributed systems. Expert in network security and cloud architecture.",
    resumeFile: "raj_k_resume.pdf",
    appliedFor: "jd-004",
    screened: "2026-04-08",
    status: "shortlisted",
    keyHighlights: [
      "Managed 500+ node Kubernetes cluster",
      "Zero-downtime deployment for critical infrastructure",
      "Cisco Certified Architect",
      "Reduced infrastructure costs by 30%",
    ],
  },
];

export const screeningStats = {
  totalScreened: 63,
  avgMatchScore: 78,
  shortlisted: 18,
  activeJobs: 3,
  screeningTime: "< 2 mins",
  topSkillsInDemand: ["Python", "React", "AWS", "TypeScript", "Docker", "Node.js", "Machine Learning"],
};
