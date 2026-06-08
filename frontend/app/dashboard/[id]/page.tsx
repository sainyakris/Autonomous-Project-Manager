"use client";

import { useEffect, useState } from "react";
import { useRouter, useParams } from "next/navigation";
import {
  getProject, getProjectTasks, getDashboard,
  runAutonomy, getNotifications, generateReport, submitUpdate
} from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ArrowLeft, Zap, Bell, FileText, RefreshCw } from "lucide-react";

export default function ProjectDetail() {
  const router = useRouter();
  const params = useParams();
  const projectId = params.id as string;

  const [project, setProject] = useState<any>(null);
  const [tasks, setTasks] = useState<any[]>([]);
  const [dashboard, setDashboard] = useState<any>(null);
  const [notifications, setNotifications] = useState<any[]>([]);
  const [report, setReport] = useState<any>(null);
  const [autonomyResult, setAutonomyResult] = useState<any>(null);

  const [loadingAutonomy, setLoadingAutonomy] = useState(false);
  const [loadingReport, setLoadingReport] = useState(false);

  // Update submission
  const [selectedTask, setSelectedTask] = useState("");
  const [updateText, setUpdateText] = useState("");
  const [submittingUpdate, setSubmittingUpdate] = useState(false);
  const [updateSuccess, setUpdateSuccess] = useState(false);

  useEffect(() => {
    fetchAll();
  }, []);

  const fetchAll = async () => {
    try {
      const [projRes, tasksRes, dashRes, notifRes] = await Promise.all([
        getProject(projectId),
        getProjectTasks(projectId),
        getDashboard(projectId),
        getNotifications(),
      ]);
      setProject(projRes.data);
      setTasks(tasksRes.data);
      setDashboard(dashRes.data);
      setNotifications(notifRes.data.notifications);
    } catch {
      router.push("/dashboard");
    }
  };

  const handleRunAutonomy = async () => {
    setLoadingAutonomy(true);
    try {
      const res = await runAutonomy(projectId);
      setAutonomyResult(res.data);
      const notifRes = await getNotifications();
      setNotifications(notifRes.data.notifications);
    } catch (e) {
      console.error(e);
    } finally {
      setLoadingAutonomy(false);
    }
  };

  const handleGenerateReport = async () => {
    setLoadingReport(true);
    try {
      const res = await generateReport(projectId);
      setReport(res.data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoadingReport(false);
    }
  };

  const handleSubmitUpdate = async () => {
    if (!selectedTask || !updateText) return;
    setSubmittingUpdate(true);
    try {
      await submitUpdate(selectedTask, updateText);
      setUpdateText("");
      setUpdateSuccess(true);
      setTimeout(() => setUpdateSuccess(false), 3000);
      fetchAll();
    } catch (e) {
      console.error(e);
    } finally {
      setSubmittingUpdate(false);
    }
  };

  const getPriorityColor = (priority: string) => {
    if (priority === "critical") return "destructive";
    if (priority === "high") return "secondary";
    return "outline";
  };

  const getHealthColor = (health: string) => {
    if (health === "red") return "text-red-500";
    if (health === "yellow") return "text-yellow-500";
    return "text-green-500";
  };

  if (!project) return (
    <div className="min-h-screen flex items-center justify-center text-slate-400">
      Loading...
    </div>
  );

  return (
    <main className="min-h-screen bg-slate-50">
      {/* Header */}
      <div className="bg-white border-b border-slate-200 px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Button variant="ghost" size="sm" onClick={() => router.push("/dashboard")}>
            <ArrowLeft className="w-4 h-4" />
          </Button>
          <div>
            <h1 className="font-semibold text-slate-900">{project.name}</h1>
            <p className="text-xs text-slate-400">{project.status} · {project.risk_level} risk</p>
          </div>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={handleRunAutonomy} disabled={loadingAutonomy}>
            <Zap className="w-4 h-4 mr-2" />
            {loadingAutonomy ? "Running..." : "Run Autonomy"}
          </Button>
          <Button variant="outline" size="sm" onClick={handleGenerateReport} disabled={loadingReport}>
            <FileText className="w-4 h-4 mr-2" />
            {loadingReport ? "Generating..." : "Client Report"}
          </Button>
        </div>
      </div>

      <div className="max-w-5xl mx-auto px-6 py-8">
        {/* Stats row */}
        {dashboard && (
          <div className="grid grid-cols-4 gap-4 mb-8">
            <Card>
              <CardContent className="pt-5">
                <div className="text-2xl font-bold text-slate-900">
                  {Math.round(dashboard.project.progress * 100)}%
                </div>
                <div className="text-xs text-slate-400 mt-1">Progress</div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-5">
                <div className={`text-2xl font-bold ${getHealthColor(dashboard.health)}`}>
                  {dashboard.health.toUpperCase()}
                </div>
                <div className="text-xs text-slate-400 mt-1">Health</div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-5">
                <div className="text-2xl font-bold text-slate-900">
                  {dashboard.task_summary.done}/{dashboard.task_summary.total}
                </div>
                <div className="text-xs text-slate-400 mt-1">Tasks done</div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-5">
                <div className="text-2xl font-bold text-slate-900">
                  {Math.round(project.autonomy_score * 100)}%
                </div>
                <div className="text-xs text-slate-400 mt-1">Autonomy score</div>
              </CardContent>
            </Card>
          </div>
        )}

        <Tabs defaultValue="tasks">
          <TabsList className="mb-6">
            <TabsTrigger value="tasks">Tasks</TabsTrigger>
            <TabsTrigger value="updates">Submit Update</TabsTrigger>
            <TabsTrigger value="autonomy">Autonomy</TabsTrigger>
            <TabsTrigger value="notifications">
              Notifications {notifications.length > 0 && `(${notifications.length})`}
            </TabsTrigger>
            <TabsTrigger value="report">Client Report</TabsTrigger>
          </TabsList>

          {/* Tasks tab */}
          <TabsContent value="tasks" className="space-y-3">
            {tasks.map((task) => (
              <Card key={task.id}>
                <CardContent className="py-4 px-5">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="font-medium text-sm text-slate-900">{task.title}</span>
                        <Badge variant={getPriorityColor(task.priority) as any} className="text-xs">
                          {task.priority}
                        </Badge>
                        {task.ai_generated && (
                          <Badge variant="outline" className="text-xs">AI</Badge>
                        )}
                      </div>
                      <p className="text-xs text-slate-500">{task.description}</p>
                      {task.required_skills?.length > 0 && (
                        <div className="flex gap-1 mt-2">
                          {task.required_skills.map((s: string) => (
                            <span key={s} className="text-xs bg-slate-100 text-slate-600 px-2 py-0.5 rounded">
                              {s}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                    <div className="text-right ml-4 shrink-0">
                      <div className="text-xs font-medium text-slate-700">{task.status}</div>
                      <div className="text-xs text-slate-400">{task.estimated_hours}h est.</div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </TabsContent>

          {/* Submit update tab */}
          <TabsContent value="updates">
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Submit a task update</CardTitle>
                <CardDescription>
                  Write in plain English — the AI will extract progress, blockers and sentiment.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <label className="text-sm font-medium text-slate-700">Select task</label>
                  <select
                    className="w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-slate-400"
                    value={selectedTask}
                    onChange={(e) => setSelectedTask(e.target.value)}
                  >
                    <option value="">Choose a task...</option>
                    {tasks.map((t) => (
                      <option key={t.id} value={t.id}>{t.title}</option>
                    ))}
                  </select>
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium text-slate-700">Update</label>
                  <textarea
                    className="w-full min-h-[100px] rounded-md border border-slate-200 bg-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-slate-400 resize-none"
                    placeholder="e.g. I finished the login page but hit a CSS bug on mobile..."
                    value={updateText}
                    onChange={(e) => setUpdateText(e.target.value)}
                  />
                </div>
                {updateSuccess && (
                  <p className="text-sm text-green-600">Update submitted and parsed successfully.</p>
                )}
                <Button onClick={handleSubmitUpdate} disabled={submittingUpdate}>
                  {submittingUpdate ? "Submitting..." : "Submit update"}
                </Button>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Autonomy tab */}
          <TabsContent value="autonomy" className="space-y-4">
            {!autonomyResult ? (
              <Card>
                <CardContent className="py-12 text-center">
                  <Zap className="w-8 h-8 text-slate-300 mx-auto mb-3" />
                  <p className="text-slate-500 text-sm">Run the autonomy engine to see AI decisions.</p>
                  <Button className="mt-4" onClick={handleRunAutonomy} disabled={loadingAutonomy}>
                    {loadingAutonomy ? "Running..." : "Run Autonomy Engine"}
                  </Button>
                </CardContent>
              </Card>
            ) : (
              <>
                <div className="grid grid-cols-3 gap-4">
                  <Card>
                    <CardContent className="pt-5">
                      <div className="text-2xl font-bold text-slate-900">{autonomyResult.decisions_made}</div>
                      <div className="text-xs text-slate-400 mt-1">Decisions made</div>
                    </CardContent>
                  </Card>
                  <Card>
                    <CardContent className="pt-5">
                      <div className="text-2xl font-bold text-green-600">{autonomyResult.executed_autonomously}</div>
                      <div className="text-xs text-slate-400 mt-1">Acted autonomously</div>
                    </CardContent>
                  </Card>
                  <Card>
                    <CardContent className="pt-5">
                      <div className="text-2xl font-bold text-yellow-600">{autonomyResult.escalated_to_human}</div>
                      <div className="text-xs text-slate-400 mt-1">Escalated to you</div>
                    </CardContent>
                  </Card>
                </div>

                <Card>
                  <CardHeader>
                    <CardTitle className="text-sm">Observations</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <ul className="space-y-1">
                      {autonomyResult.observations.map((obs: string, i: number) => (
                        <li key={i} className="text-sm text-slate-600 flex gap-2">
                          <span className="text-slate-300">—</span> {obs}
                        </li>
                      ))}
                    </ul>
                  </CardContent>
                </Card>

                {autonomyResult.executed_decisions.length > 0 && (
                  <Card>
                    <CardHeader>
                      <CardTitle className="text-sm text-green-700">✓ Executed Autonomously</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-3">
                      {autonomyResult.executed_decisions.map((d: any, i: number) => (
                        <div key={i} className="text-sm border-l-2 border-green-200 pl-3">
                          <div className="font-medium text-slate-800">{d.action.description}</div>
                          <div className="text-slate-400 text-xs mt-0.5">
                            Confidence: {Math.round(d.confidence * 100)}% · {d.type}
                          </div>
                        </div>
                      ))}
                    </CardContent>
                  </Card>
                )}

                {autonomyResult.escalated_decisions.length > 0 && (
                  <Card>
                    <CardHeader>
                      <CardTitle className="text-sm text-yellow-700">⚠ Escalated to You</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-3">
                      {autonomyResult.escalated_decisions.map((d: any, i: number) => (
                        <div key={i} className="text-sm border-l-2 border-yellow-200 pl-3">
                          <div className="font-medium text-slate-800">{d.action.description}</div>
                          <div className="text-slate-400 text-xs mt-0.5">
                            Confidence: {Math.round(d.confidence * 100)}% — needs your input
                          </div>
                        </div>
                      ))}
                    </CardContent>
                  </Card>
                )}
              </>
            )}
          </TabsContent>

          {/* Notifications tab */}
          <TabsContent value="notifications" className="space-y-3">
            {notifications.length === 0 ? (
              <Card>
                <CardContent className="py-12 text-center text-slate-400 text-sm">
                  No notifications yet. Run the autonomy engine to generate some.
                </CardContent>
              </Card>
            ) : (
              notifications.map((n) => (
                <Card key={n.id} className={n.level === "warning" ? "border-yellow-200" : ""}>
                  <CardContent className="py-4 px-5">
                    <div className="flex items-start justify-between">
                      <div>
                        <div className="font-medium text-sm text-slate-900">{n.title}</div>
                        <div className="text-xs text-slate-500 mt-1">{n.message}</div>
                      </div>
                      <Badge variant={n.autonomous ? "default" : "secondary"} className="text-xs shrink-0 ml-4">
                        {n.autonomous ? "Auto" : "Escalated"}
                      </Badge>
                    </div>
                  </CardContent>
                </Card>
              ))
            )}
          </TabsContent>

          {/* Client report tab */}
          <TabsContent value="report">
            {!report ? (
              <Card>
                <CardContent className="py-12 text-center">
                  <FileText className="w-8 h-8 text-slate-300 mx-auto mb-3" />
                  <p className="text-slate-500 text-sm">Generate a professional client report.</p>
                  <Button className="mt-4" onClick={handleGenerateReport} disabled={loadingReport}>
                    {loadingReport ? "Generating..." : "Generate Report"}
                  </Button>
                </CardContent>
              </Card>
            ) : (
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">{report.subject}</CardTitle>
                  <div className="flex gap-2 mt-1">
                    <Badge variant="outline">{report.tone}</Badge>
                  </div>
                </CardHeader>
                <CardContent className="space-y-4">
                  <p className="text-sm text-slate-700 leading-relaxed">{report.report}</p>
                  {report.key_wins?.length > 0 && (
                    <div>
                      <div className="text-xs font-medium text-slate-500 mb-2">KEY WINS</div>
                      <ul className="space-y-1">
                        {report.key_wins.map((w: string, i: number) => (
                          <li key={i} className="text-sm text-slate-600 flex gap-2">
                            <span className="text-green-500">✓</span> {w}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                  {report.next_milestone && (
                    <div className="bg-slate-50 rounded-lg p-3">
                      <div className="text-xs font-medium text-slate-500 mb-1">NEXT MILESTONE</div>
                      <div className="text-sm text-slate-700">{report.next_milestone}</div>
                    </div>
                  )}
                  <Button variant="outline" size="sm" onClick={handleGenerateReport} disabled={loadingReport}>
                    <RefreshCw className="w-3 h-3 mr-2" />
                    Regenerate
                  </Button>
                </CardContent>
              </Card>
            )}
          </TabsContent>
        </Tabs>
      </div>
    </main>
  );
}