"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { getProjects, createProject } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Plus, LogOut, Zap } from "lucide-react";

interface Project {
  id: string;
  name: string;
  description: string;
  status: string;
  progress: number;
  risk_level: string;
  autonomy_score: number;
  created_at: string;
}

export default function Dashboard() {
  const router = useRouter();
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [showForm, setShowForm] = useState(false);

  // New project form
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [deadlineDays, setDeadlineDays] = useState("");

  useEffect(() => {
    const token = localStorage.getItem("token");
    if (!token) {
      router.push("/");
      return;
    }
    fetchProjects();
  }, []);

  const fetchProjects = async () => {
    try {
      const res = await getProjects();
      setProjects(res.data);
    } catch {
      router.push("/");
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async () => {
    if (!name || !description) return;
    setCreating(true);
    try {
      await createProject(name, description, deadlineDays ? parseInt(deadlineDays) : undefined);
      setName("");
      setDescription("");
      setDeadlineDays("");
      setShowForm(false);
      fetchProjects();
    } catch (e) {
      console.error(e);
    } finally {
      setCreating(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem("token");
    router.push("/");
  };

  const getRiskColor = (risk: string) => {
    if (risk === "high") return "destructive";
    if (risk === "medium") return "secondary";
    return "outline";
  };

  return (
    <main className="min-h-screen bg-slate-50">
      {/* Header */}
      <div className="bg-white border-b border-slate-200 px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Zap className="w-5 h-5 text-slate-900" />
          <h1 className="text-lg font-semibold text-slate-900">AutonomousPM</h1>
        </div>
        <Button variant="ghost" size="sm" onClick={handleLogout}>
          <LogOut className="w-4 h-4 mr-2" />
          Logout
        </Button>
      </div>

      <div className="max-w-5xl mx-auto px-6 py-8">
        {/* Page header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h2 className="text-2xl font-bold text-slate-900">Projects</h2>
            <p className="text-slate-500 text-sm mt-1">
              {projects.length} project{projects.length !== 1 ? "s" : ""}
            </p>
          </div>
          <Button onClick={() => setShowForm(!showForm)}>
            <Plus className="w-4 h-4 mr-2" />
            New Project
          </Button>
        </div>

        {/* Create project form */}
        {showForm && (
          <Card className="mb-6 border-slate-200">
            <CardHeader>
              <CardTitle className="text-base">Create a new project</CardTitle>
              <CardDescription>
                Describe your project and the AI will generate tasks automatically.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label>Project name</Label>
                <Input
                  placeholder="e.g. E-commerce Website"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                />
              </div>
              <div className="space-y-2">
                <Label>Description</Label>
                <textarea
                  className="w-full min-h-[100px] rounded-md border border-slate-200 bg-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-slate-400 resize-none"
                  placeholder="Describe what you want to build in plain English..."
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                />
              </div>
              <div className="space-y-2">
                <Label>Deadline (days from today) — optional</Label>
                <Input
                  type="number"
                  placeholder="e.g. 30"
                  value={deadlineDays}
                  onChange={(e) => setDeadlineDays(e.target.value)}
                />
              </div>
              <div className="flex gap-2">
                <Button onClick={handleCreate} disabled={creating}>
                  {creating ? "Creating — AI generating tasks..." : "Create project"}
                </Button>
                <Button variant="outline" onClick={() => setShowForm(false)}>
                  Cancel
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Projects list */}
        {loading ? (
          <div className="text-center py-20 text-slate-400">Loading projects...</div>
        ) : projects.length === 0 ? (
          <div className="text-center py-20">
            <p className="text-slate-400 text-sm">No projects yet.</p>
            <p className="text-slate-400 text-sm mt-1">Create one above to get started.</p>
          </div>
        ) : (
          <div className="grid gap-4">
            {projects.map((project) => (
              <Card
                key={project.id}
                className="cursor-pointer hover:border-slate-300 transition-colors"
                onClick={() => router.push(`/dashboard/${project.id}`)}
              >
                <CardContent className="py-5 px-6">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <h3 className="font-medium text-slate-900">{project.name}</h3>
                        <Badge variant={getRiskColor(project.risk_level) as any}>
                          {project.risk_level} risk
                        </Badge>
                      </div>
                      <p className="text-sm text-slate-500 line-clamp-1">{project.description}</p>
                    </div>
                    <div className="text-right ml-6">
                      <div className="text-sm font-medium text-slate-900">
                        {Math.round(project.progress * 100)}%
                      </div>
                      <div className="text-xs text-slate-400">progress</div>
                    </div>
                  </div>
                  {/* Progress bar */}
                  <div className="mt-3 h-1.5 bg-slate-100 rounded-full">
                    <div
                      className="h-1.5 bg-slate-900 rounded-full transition-all"
                      style={{ width: `${project.progress * 100}%` }}
                    />
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>
    </main>
  );
}