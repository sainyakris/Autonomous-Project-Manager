import axios from "axios";

const API_BASE = "http://localhost:8000/api/v1";

const api = axios.create({
  baseURL: API_BASE,
});

// Automatically attach JWT token to every request
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Auth
export const login = (email: string, password: string) =>
  api.post("/auth/login", { email, password });

export const register = (name: string, email: string, password: string, skills: string[]) =>
  api.post("/auth/register", { name, email, password, skills });

// Projects
export const getProjects = () => api.get("/projects/");
export const createProject = (name: string, description: string, deadline_days?: number) =>
  api.post("/projects/", { name, description, deadline_days });
export const getProject = (id: string) => api.get(`/projects/${id}`);
export const getProjectTasks = (id: string) => api.get(`/projects/${id}/tasks`);

// Updates
export const submitUpdate = (task_id: string, text: string) =>
  api.post("/updates/", { task_id, text });

// Dashboard
export const getDashboard = (project_id: string) =>
  api.get(`/dashboard/${project_id}`);
export const generateReport = (project_id: string) =>
  api.post("/dashboard/report/generate", { project_id });

// Autonomy
export const runAutonomy = (project_id: string) =>
  api.post(`/autonomy/run/${project_id}`);
export const getNotifications = () => api.get("/autonomy/notifications");

export default api;