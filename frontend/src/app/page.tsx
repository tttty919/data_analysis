"use client";
import { useState, useEffect, useCallback } from "react";
import { uploadFile, getDatasets, createTask, getTasks, deleteTask, testApiKey, getTaskDetail, getTaskReport, downloadUrl, chartUrl } from "@/lib/api";
import { useTaskPolling } from "@/hooks/useTaskPolling";
import type { Task, DatasetItem, UploadResult, AnalysisResults } from "@/lib/types";
import { NPSPanel, PainPointsPanel, CompetitorPanel, SegmentsPanel, JTBDPanel, JourneyPanel } from "./content-panels";

const TASK_TYPE_LABELS: Record<string, string> = {
  exploration: "数据探索", modeling: "智能建模", content_analysis: "内容分析", prediction: "预测分析",
};

export default function Home() {
  const [activeTaskId, setActiveTaskId] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState("eda");
  const [tasks, setTasks] = useState<Task[]>([]);
  const [taskDetail, setTaskDetail] = useState<Task | null>(null);
  const [taskResults, setTaskResults] = useState<AnalysisResults | null>(null);
  const [datasets, setDatasets] = useState<DatasetItem[]>([]);
  const [apiKey, setApiKey] = useState("");
  const [taskType, setTaskType] = useState("exploration");
  const [userInput, setUserInput] = useState("");
  const [selectedDataset, setSelectedDataset] = useState<string>("");
  const [createLoading, setCreateLoading] = useState(false);
  const [uploadedFileId, setUploadedFileId] = useState<string>("");
  const [uploadedFileName, setUploadedFileName] = useState<string>("");
  const [uploadPreview, setUploadPreview] = useState<UploadResult | null>(null);
  const [textColumn, setTextColumn] = useState("");
  const [sidebarSection, setSidebarSection] = useState<"create" | "history">("create");

  const { progress, isComplete } = useTaskPolling(
    activeTaskId,
    !!(activeTaskId && taskDetail && !["completed", "failed", "stopped"].includes(taskDetail.status))
  );

  useEffect(() => { getDatasets().then(setDatasets).catch(() => {}); }, []);
  useEffect(() => { setApiKey(localStorage.getItem("ds_api_key") || ""); }, []);
  useEffect(() => { loadTasks(); }, []);

  useEffect(() => {
    if (progress && taskDetail) {
      setTaskDetail((prev) => prev ? { ...prev, progress, phase: progress.phase, status: progress.status || prev.status } : prev);
    }
  }, [progress]);

  useEffect(() => {
    if (isComplete && activeTaskId) {
      getTaskDetail(activeTaskId).then(setTaskDetail).catch(() => {});
      getTaskReport(activeTaskId).then(setTaskResults).catch(() => {});
      loadTasks();
    }
  }, [isComplete, activeTaskId]);

  const loadTasks = async () => {
    try { setTasks(await getTasks()); } catch {}
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    try {
      const result = await uploadFile(file);
      setUploadedFileId(result.task_id);
      setUploadedFileName(result.filename);
      setUploadPreview(result);
      setSelectedDataset("");
    } catch (err: unknown) {
      alert("上传失败: " + (err instanceof Error ? err.message : String(err)));
    }
  };

  const handleSelectDataset = (name: string) => {
    setSelectedDataset(name);
    setUploadedFileId("");
    setUploadedFileName("");
    setUploadPreview(null);
  };

  const handleCreateTask = async () => {
    const dataSource = selectedDataset || uploadedFileId;
    if (!dataSource) { alert("请上传文件或选择示例数据集"); return; }
    if (apiKey) localStorage.setItem("ds_api_key", apiKey);

    setCreateLoading(true);
    try {
      const { task_id } = await createTask({
        task_type: taskType,
        data_source: dataSource,
        requirements: { user_input: userInput, target_column: "", text_column: textColumn },
        api_key: apiKey || undefined,
      });
      setActiveTaskId(task_id);
      const detail = await getTaskDetail(task_id);
      setTaskDetail(detail);
      setTaskResults(null);
      setActiveTab(detail.task_type === "content_analysis" ? "content" : "eda");
      loadTasks();
    } catch (err: unknown) {
      alert("创建失败: " + (err instanceof Error ? err.message : String(err)));
    }
    setCreateLoading(false);
  };

  const handleSelectTask = async (taskId: string) => {
    setActiveTaskId(taskId);
    try {
      const detail = await getTaskDetail(taskId);
      setTaskDetail(detail);
      setActiveTab(detail.task_type === "content_analysis" ? "content" : "eda");
      if (["completed"].includes(detail.status)) {
        const results = await getTaskReport(taskId);
        setTaskResults(results);
      } else {
        setTaskResults(null);
      }
    } catch { setTaskDetail(null); setTaskResults(null); }
  };

  const handleDeleteTask = async (taskId: string) => {
    try {
      await deleteTask(taskId);
      if (activeTaskId === taskId) { setActiveTaskId(null); setTaskDetail(null); setTaskResults(null); }
      loadTasks();
    } catch (err: unknown) { alert("删除失败: " + (err instanceof Error ? err.message : String(err))); }
  };

  const handleTestApiKey = async () => {
    if (!apiKey) return;
    try {
      const r = await testApiKey(apiKey);
      alert(r.message);
    } catch (err: unknown) { alert("测试失败: " + (err instanceof Error ? err.message : String(err))); }
  };

  return (
    <>
      {/* Sidebar */}
      <aside className="w-[340px] bg-white border-r border-gray-200 flex flex-col h-full shrink-0">
        <div className="p-5 border-b border-gray-100">
          <h1 className="text-lg font-bold text-[#6366f1]">智能数据分析系统</h1>
          <p className="text-xs text-gray-400 mt-1">上传数据 · 自动分析 · 洞察输出</p>
        </div>

        {/* Tab switcher */}
        <div className="flex border-b border-gray-100">
          <button onClick={() => setSidebarSection("create")}
            className={`flex-1 py-3 text-sm font-medium ${sidebarSection === "create" ? "text-[#6366f1] border-b-2 border-[#6366f1]" : "text-gray-400"}`}>
            新建任务
          </button>
          <button onClick={() => { setSidebarSection("history"); loadTasks(); }}
            className={`flex-1 py-3 text-sm font-medium ${sidebarSection === "history" ? "text-[#6366f1] border-b-2 border-[#6366f1]" : "text-gray-400"}`}>
            历史记录
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {sidebarSection === "create" ? (
            <>
              {/* Data Source */}
              <div className="bg-gray-50 rounded-lg p-3">
                <h3 className="text-xs font-semibold text-gray-500 mb-2">数据来源</h3>

                <label className="block border-2 border-dashed border-gray-300 rounded-lg p-4 text-center cursor-pointer hover:border-[#6366f1] transition-colors mb-3">
                  <input type="file" accept=".csv,.xlsx,.xls" onChange={handleFileUpload} className="hidden" />
                  <div className="text-2xl mb-1">📁</div>
                  <div className="text-sm text-gray-600">{uploadedFileName || "点击上传 CSV / Excel"}</div>
                  <div className="text-xs text-gray-400 mt-1">支持 .csv .xlsx .xls</div>
                </label>

                <div className="text-xs text-gray-400 mb-2 text-center">或选择示例数据集</div>
                <div className="grid grid-cols-2 gap-2">
                  {datasets.map((ds) => (
                    <button key={ds.name} onClick={() => handleSelectDataset(ds.name)}
                      className={`text-left p-2 rounded-lg border text-xs transition-colors ${selectedDataset === ds.name ? "border-[#6366f1] bg-indigo-50" : "border-gray-200 hover:border-gray-300"}`}>
                      <div className="font-medium text-gray-700">{ds.name}</div>
                      <div className="text-gray-400">{ds.row_count}行</div>
                    </button>
                  ))}
                </div>
                {uploadPreview && (
                  <div className="mt-2 text-xs text-gray-500">
                    已上传: {uploadPreview.total_rows}行 × {uploadPreview.headers.length}列
                  </div>
                )}
              </div>

              {/* Task Type */}
              <div className="bg-gray-50 rounded-lg p-3">
                <h3 className="text-xs font-semibold text-gray-500 mb-2">分析类型</h3>
                <select value={taskType} onChange={(e) => setTaskType(e.target.value)}
                  className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm bg-white">
                  <option value="exploration">数据探索 (EDA + 可视化)</option>
                  <option value="modeling">智能建模 (AutoML)</option>
                  <option value="content_analysis">内容分析 (AI 文本解读)</option>
                </select>
              </div>

              {/* Text column selector for content analysis */}
              {taskType === "content_analysis" && uploadPreview && (
                <div className="bg-gray-50 rounded-lg p-3">
                  <h3 className="text-xs font-semibold text-gray-500 mb-2">文本列（选择要分析的内容列）</h3>
                  <select value={textColumn} onChange={(e) => setTextColumn(e.target.value)}
                    className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm bg-white">
                    <option value="">自动检测</option>
                    {uploadPreview.headers.filter(h => uploadPreview.col_types[h] === "categorical").map(h => (
                      <option key={h} value={h}>{h}</option>
                    ))}
                  </select>
                </div>
              )}

              {/* NLU Input */}
              <div className="bg-gray-50 rounded-lg p-3">
                <h3 className="text-xs font-semibold text-gray-500 mb-2">分析需求（可选）</h3>
                <textarea value={userInput} onChange={(e) => setUserInput(e.target.value)}
                  placeholder={taskType === "content_analysis" ? "例如：帮我分析用户评论的情感倾向和主要投诉点..." : "例如：帮我分析销售趋势，并预测下季度利润..."}
                  className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm resize-none h-20"
                />
              </div>

              {/* API Key */}
              <div className="bg-gray-50 rounded-lg p-3">
                <h3 className="text-xs font-semibold text-gray-500 mb-2">DeepSeek API Key（可选）</h3>
                <div className="flex gap-2">
                  <input type="password" value={apiKey} onChange={(e) => setApiKey(e.target.value)}
                    placeholder="sk-..." className="flex-1 border border-gray-200 rounded-lg px-3 py-2 text-sm" />
                  <button onClick={handleTestApiKey}
                    className="px-3 py-2 text-xs border border-gray-200 rounded-lg hover:bg-gray-100">测试</button>
                </div>
              </div>

              {/* Create Button */}
              <button onClick={handleCreateTask} disabled={createLoading}
                className="w-full py-3 bg-[#6366f1] text-white rounded-lg font-medium hover:bg-[#4f46e5] disabled:opacity-50 transition-colors">
                {createLoading ? "创建中..." : "开始分析"}
              </button>
            </>
          ) : (
            /* History */
            <div className="space-y-2">
              {tasks.length === 0 && <div className="text-sm text-gray-400 text-center py-8">暂无任务</div>}
              {tasks.map((t) => (
                <div key={t.task_id}
                  onClick={() => handleSelectTask(t.task_id)}
                  className={`p-3 rounded-lg cursor-pointer border transition-colors ${activeTaskId === t.task_id ? "border-[#6366f1] bg-indigo-50" : "border-gray-100 hover:border-gray-200"}`}>
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium">{t.task_id}</span>
                    <span className={`text-xs px-2 py-0.5 rounded-full ${
                      t.status === "completed" ? "bg-green-100 text-green-700" :
                      t.status === "running" ? "bg-blue-100 text-blue-700" :
                      t.status === "failed" ? "bg-red-100 text-red-700" : "bg-gray-100 text-gray-600"
                    }`}>
                      {t.status === "completed" ? "完成" : t.status === "running" ? "运行中" : t.status === "failed" ? "失败" : t.status}
                    </span>
                  </div>
                  <div className="text-xs text-gray-400 mt-1">{TASK_TYPE_LABELS[t.task_type] || t.task_type} · {t.created_at?.slice(0, 16)}</div>
                  <button onClick={(e) => { e.stopPropagation(); handleDeleteTask(t.task_id); }}
                    className="text-xs text-gray-400 hover:text-red-500 mt-1">删除</button>
                </div>
              ))}
            </div>
          )}
        </div>
      </aside>

      {/* Main Area */}
      <main className="flex-1 overflow-y-auto p-6">
        {!activeTaskId && !taskDetail && (
          <div className="flex flex-col items-center justify-center h-full text-gray-400">
            <div className="text-6xl mb-4">📊</div>
            <div className="text-lg font-medium mb-2">智能数据分析系统</div>
            <div className="text-sm">上传数据或选择示例数据集，开始自动分析</div>
          </div>
        )}

        {/* Progress */}
        {taskDetail && taskDetail.status === "running" && taskDetail.progress && (
          <div className="mb-6 bg-white rounded-xl p-6 shadow-sm border border-gray-100">
            <div className="flex items-center gap-3 mb-3">
              <div className="animate-spin text-xl">⚡</div>
              <div>
                <div className="font-medium text-gray-700">{taskDetail.progress.current_step}</div>
                <div className="text-sm text-gray-400">{taskDetail.progress.message}</div>
              </div>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div className="bg-[#6366f1] h-2 rounded-full transition-all duration-500"
                style={{ width: `${taskDetail.progress.progress_pct}%` }} />
            </div>
            <div className="text-xs text-gray-400 mt-1 text-right">{Math.round(taskDetail.progress.progress_pct)}%</div>
          </div>
        )}

        {/* Error */}
        {taskDetail && taskDetail.status === "failed" && (
          <div className="mb-6 bg-red-50 border border-red-200 rounded-xl p-6">
            <div className="font-medium text-red-700 mb-1">分析失败</div>
            <div className="text-sm text-red-600">{taskDetail.error || "未知错误"}</div>
          </div>
        )}

        {/* Results */}
        {taskDetail && taskDetail.status === "completed" && taskResults && (
          <div>
            {/* Toolbar */}
            <div className="flex items-center justify-between mb-6">
              <div>
                <h2 className="text-xl font-bold text-gray-800">分析结果</h2>
                <p className="text-sm text-gray-400">任务 {taskDetail.task_id} · {taskDetail.created_at?.slice(0, 16)}</p>
              </div>
              <div className="flex gap-2">
                <a href={downloadUrl(taskDetail.task_id, "html")} target="_blank"
                  className="px-4 py-2 text-sm border border-gray-200 rounded-lg hover:bg-gray-50">HTML报告</a>
                <a href={downloadUrl(taskDetail.task_id, "excel")}
                  className="px-4 py-2 text-sm border border-gray-200 rounded-lg hover:bg-gray-50">Excel报告</a>
              </div>
            </div>

            {/* Executive Summary */}
            {taskResults.report && (
              <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100 mb-6">
                <h3 className="font-semibold text-gray-700 mb-3">执行摘要</h3>
                <div className="text-sm text-gray-600 leading-relaxed whitespace-pre-wrap">
                  {taskResults.report.executive_summary}
                </div>
              </div>
            )}

            {/* Tabs */}
            {taskResults && (
              <TabsSection taskDetail={taskDetail} taskResults={taskResults}
                activeTab={activeTab} setActiveTab={setActiveTab} />
            )}
          </div>
        )}
      </main>
    </>
  );
}

/* ====== Tab Panels ====== */

function EDAPanel({ results }: { results: AnalysisResults }) {
  const qa = results.quality_analysis;
  const stats = results.statistical_analysis;
  const outliers = results.outlier_analysis;
  if (!qa && !stats) return <div className="text-gray-400 text-center py-8">暂无数据探索结果</div>;

  return (
    <div className="space-y-6">
      {/* Quality Cards */}
      <div className="grid grid-cols-4 gap-4">
        <Card label="总行数" value={String(results.basic_info?.row_count || "-")} />
        <Card label="总列数" value={String(results.basic_info?.column_count || "-")} />
        <Card label="缺失比例" value={qa ? `${(qa.missing_cells / Math.max(qa.total_cells, 1) * 100).toFixed(1)}%` : "-"} />
        <Card label="重复比例" value={qa ? `${qa.duplicate_percentage.toFixed(1)}%` : "-"} />
      </div>

      {/* Statistics Table */}
      {stats && Object.keys(stats).length > 0 && (
        <div>
          <h4 className="font-semibold text-gray-700 mb-3">描述性统计</h4>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-gray-50">
                  <th className="text-left p-2 font-medium text-gray-500">列名</th>
                  <th className="text-right p-2 font-medium text-gray-500">均值</th>
                  <th className="text-right p-2 font-medium text-gray-500">标准差</th>
                  <th className="text-right p-2 font-medium text-gray-500">最小值</th>
                  <th className="text-right p-2 font-medium text-gray-500">中位数</th>
                  <th className="text-right p-2 font-medium text-gray-500">最大值</th>
                  <th className="text-right p-2 font-medium text-gray-500">偏度</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(stats).slice(0, 15).map(([col, s]) => (
                  <tr key={col} className="border-t border-gray-50">
                    <td className="p-2 font-medium">{col}</td>
                    <td className="text-right p-2">{s.mean?.toFixed(2)}</td>
                    <td className="text-right p-2">{s.std?.toFixed(2)}</td>
                    <td className="text-right p-2">{s.min?.toFixed(2)}</td>
                    <td className="text-right p-2">{s.median?.toFixed(2)}</td>
                    <td className="text-right p-2">{s.max?.toFixed(2)}</td>
                    <td className="text-right p-2">{s.skewness?.toFixed(2)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Outliers */}
      {outliers && Object.keys(outliers).length > 0 && (
        <div>
          <h4 className="font-semibold text-gray-700 mb-3">异常值检测 (IQR方法)</h4>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-gray-50">
                  <th className="text-left p-2 font-medium text-gray-500">列名</th>
                  <th className="text-right p-2 font-medium text-gray-500">异常值数</th>
                  <th className="text-right p-2 font-medium text-gray-500">比例</th>
                  <th className="text-right p-2 font-medium text-gray-500">下界</th>
                  <th className="text-right p-2 font-medium text-gray-500">上界</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(outliers).map(([col, o]) => (
                  <tr key={col} className="border-t border-gray-50">
                    <td className="p-2 font-medium">{col}</td>
                    <td className="text-right p-2">{o.outlier_count}</td>
                    <td className="text-right p-2">{o.outlier_percentage.toFixed(1)}%</td>
                    <td className="text-right p-2">{o.lower_bound.toFixed(2)}</td>
                    <td className="text-right p-2">{o.upper_bound.toFixed(2)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}

function TabsSection({ taskDetail, taskResults, activeTab, setActiveTab }: {
  taskDetail: Task; taskResults: AnalysisResults; activeTab: string; setActiveTab: (t: string) => void;
}) {
  const isContent = taskDetail.task_type === "content_analysis";
  const tabs = isContent
    ? [
        { key: "content", label: "总览", icon: "📝" },
        { key: "nps", label: "NPS", icon: "📊" },
        { key: "pain_points", label: "痛点矩阵", icon: "🔴" },
        { key: "competitors", label: "竞品提及", icon: "🏢" },
        { key: "segments", label: "用户分群", icon: "👥" },
        { key: "jtbd", label: "JTBD", icon: "🎯" },
        { key: "journey", label: "用户旅程", icon: "🗺️" },
        { key: "insights", label: "AI 洞察", icon: "🤖" },
      ]
    : [
        { key: "eda", label: "数据探索", icon: "📊" },
        { key: "charts", label: "可视化", icon: "📈" },
        { key: "modeling", label: "建模结果", icon: "🧠" },
        { key: "insights", label: "业务洞察", icon: "💡" },
      ];

  return (
    <div className="flex gap-0 h-full">
      {/* Left tab nav */}
      <div className="w-[170px] shrink-0 border-r border-gray-100 pr-0 bg-gray-50/50 rounded-l-xl">
        <div className="p-2">
          <div className="text-xs font-semibold text-gray-400 mb-1 px-2 py-1 uppercase tracking-wider">
            {isContent ? "内容分析" : "数据分析"}
          </div>
          <div className="overflow-y-auto max-h-[calc(100vh-180px)]">
            {tabs.map((tab) => (
              <button key={tab.key} onClick={() => setActiveTab(tab.key)}
                className={`w-full text-left px-3 py-2 mb-0.5 rounded-lg text-sm font-medium transition-all ${
                  activeTab === tab.key
                    ? "bg-white text-[#6366f1] shadow-sm border border-gray-100"
                    : "text-gray-400 hover:text-gray-600 hover:bg-white/60"
                }`}>
                <span className="mr-1.5">{tab.icon}</span>{tab.label}
              </button>
            ))}
          </div>
        </div>
      </div>
      {/* Right content */}
      <div className="flex-1 bg-white rounded-r-xl p-6 shadow-sm border border-gray-100 border-l-0 overflow-y-auto">
        {isContent ? (
          <>
            {activeTab === "content" && <ContentPanel results={taskResults} taskId={taskDetail.task_id} />}
            {activeTab === "nps" && <NPSPanel results={taskResults} />}
            {activeTab === "pain_points" && <PainPointsPanel results={taskResults} />}
            {activeTab === "competitors" && <CompetitorPanel results={taskResults} />}
            {activeTab === "segments" && <SegmentsPanel results={taskResults} />}
            {activeTab === "jtbd" && <JTBDPanel results={taskResults} />}
            {activeTab === "journey" && <JourneyPanel results={taskResults} />}
            {activeTab === "insights" && <InsightsPanel results={taskResults} taskId={taskDetail.task_id} />}
          </>
        ) : (
          <>
            {activeTab === "eda" && <EDAPanel results={taskResults} />}
            {activeTab === "charts" && <ChartsPanel taskId={taskDetail.task_id} results={taskResults} />}
            {activeTab === "modeling" && <ModelingPanel results={taskResults} />}
            {activeTab === "insights" && <InsightsPanel results={taskResults} taskId={taskDetail.task_id} />}
          </>
        )}
      </div>
    </div>
  );
}

function Card({ label, value }: { label: string; value: string }) {
  return (
    <div className="bg-gray-50 rounded-xl p-4 text-center">
      <div className="text-2xl font-bold text-[#6366f1]">{value}</div>
      <div className="text-xs text-gray-400 mt-1">{label}</div>
    </div>
  );
}

function ChartsPanel({ taskId, results }: { taskId: string; results: AnalysisResults }) {
  const viz = results.visualizations || {};
  const chartNames = Object.entries(viz).filter(([, v]) => v);

  if (chartNames.length === 0) {
    return <div className="text-gray-400 text-center py-8">暂无图表</div>;
  }

  return (
    <div className="grid grid-cols-2 gap-4">
      {chartNames.map(([name, path]) => (
        <div key={name} className="border border-gray-100 rounded-xl p-4">
          <h4 className="text-sm font-medium text-gray-600 mb-2 capitalize">{name.replace(/_/g, " ")}</h4>
          <img src={chartUrl(taskId, path.replace(/\\/g, "/").split("/").pop()!)}
            alt={name} className="w-full rounded-lg" />
        </div>
      ))}
    </div>
  );
}

function ModelingPanel({ results }: { results: AnalysisResults }) {
  const models = results.model_results;
  if (!models || Object.keys(models).length === 0) {
    return <div className="text-gray-400 text-center py-8">未执行建模分析，请在创建任务时选择"智能建模"类型</div>;
  }

  const isRegression = "r2_score" in Object.values(models)[0];
  const metricKey = isRegression ? "r2_score" : "accuracy";
  const best = Object.entries(models)
    .filter(([, v]) => !v.error)
    .sort((a, b) => (b[1][metricKey] || 0) - (a[1][metricKey] || 0))[0];

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <div className="bg-green-100 text-green-700 px-3 py-1 rounded-full text-sm">
          问题类型: {isRegression ? "回归" : "分类"}
        </div>
        {best && <div className="text-sm text-gray-500">最佳模型: <strong className="text-[#6366f1]">{best[0]}</strong></div>}
      </div>

      <div>
        <h4 className="font-semibold text-gray-700 mb-3">模型对比</h4>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-gray-50">
                <th className="text-left p-2 font-medium text-gray-500">模型</th>
                <th className="text-right p-2 font-medium text-gray-500">{isRegression ? "R²" : "Accuracy"}</th>
                <th className="text-right p-2 font-medium text-gray-500">{isRegression ? "RMSE" : "F1"}</th>
                <th className="text-right p-2 font-medium text-gray-500">CV均值</th>
                <th className="text-right p-2 font-medium text-gray-500">CV标准差</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(models).map(([name, m]) => (
                <tr key={name} className={`border-t border-gray-50 ${best && best[0] === name ? "bg-green-50" : ""}`}>
                  <td className="p-2 font-medium">{name}</td>
                  <td className="text-right p-2">{"error" in m ? "-" : (m[metricKey] || 0).toFixed(4)}</td>
                  <td className="text-right p-2">{"error" in m ? "-" : ((isRegression ? m.rmse : m.f1_score) || 0).toFixed(4)}</td>
                  <td className="text-right p-2">{"error" in m ? "-" : (m.cv_mean || 0).toFixed(4)}</td>
                  <td className="text-right p-2">{"error" in m ? "-" : (m.cv_std || 0).toFixed(4)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Feature Importance */}
      {results.feature_importance && Object.keys(results.feature_importance).length > 0 && (
        <div>
          <h4 className="font-semibold text-gray-700 mb-3">特征重要性</h4>
          <div className="space-y-2 max-w-md">
            {Object.entries(results.feature_importance)
              .sort((a, b) => b[1] - a[1])
              .map(([feat, imp]) => (
                <div key={feat} className="flex items-center gap-2">
                  <span className="text-sm w-24 text-right text-gray-600 truncate">{feat}</span>
                  <div className="flex-1 bg-gray-100 rounded-full h-4">
                    <div className="bg-[#6366f1] h-4 rounded-full" style={{ width: `${Math.min((imp || 0) * 100, 100)}%` }} />
                  </div>
                  <span className="text-xs text-gray-400 w-16">{(imp || 0).toFixed(3)}</span>
                </div>
              ))}
          </div>
        </div>
      )}
    </div>
  );
}

function ContentPanel({ results, taskId }: { results: AnalysisResults; taskId: string }) {
  const content = (results as any).content_analysis;
  const keywords = (results as any).keywords || [];
  const sentiment = (results as any).sentiment;
  const themes = (results as any).themes || [];

  if (!content && !keywords.length) {
    return <div className="text-gray-400 text-center py-8">暂无内容分析结果</div>;
  }

  return (
    <div className="space-y-6">
      {/* Summary */}
      <div className="grid grid-cols-4 gap-4">
        <Card label="分析文本数" value={String(content?.total_texts || results?.total_texts || "-")} />
        <Card label="平均长度" value={content?.avg_length ? `${content.avg_length}字` : "-"} />
        <Card label="正面占比" value={sentiment ? `${(sentiment.positive_ratio * 100).toFixed(0)}%` : "-"} />
        <Card label="负面占比" value={sentiment ? `${(sentiment.negative_ratio * 100).toFixed(0)}%` : "-"} />
      </div>

      {/* Word Cloud */}
      {results.visualizations?.wordcloud && (
        <div>
          <h4 className="font-semibold text-gray-700 mb-3">关键词云</h4>
          <div className="bg-white rounded-xl border border-gray-100 p-4 flex justify-center">
            <img src={chartUrl(taskId, results.visualizations.wordcloud)}
              alt="关键词云" className="max-w-full max-h-[400px] object-contain rounded-lg" />
          </div>
        </div>
      )}

      {/* Sentiment bar */}
      {sentiment && (
        <div>
          <h4 className="font-semibold text-gray-700 mb-2">情感分析</h4>
          <div className="flex h-8 rounded-full overflow-hidden">
            <div style={{ width: `${sentiment.positive_ratio * 100}%` }}
              className="bg-green-400 flex items-center justify-center text-xs text-white font-medium">正面 {Math.round(sentiment.positive_ratio * 100)}%</div>
            <div style={{ width: `${sentiment.neutral_ratio * 100}%` }}
              className="bg-gray-300 flex items-center justify-center text-xs text-gray-600 font-medium">中性 {Math.round(sentiment.neutral_ratio * 100)}%</div>
            <div style={{ width: `${sentiment.negative_ratio * 100}%` }}
              className="bg-red-400 flex items-center justify-center text-xs text-white font-medium">负面 {Math.round(sentiment.negative_ratio * 100)}%</div>
          </div>
        </div>
      )}

      {/* Keywords */}
      {keywords.length > 0 && (
        <div>
          <h4 className="font-semibold text-gray-700 mb-3">高频关键词</h4>
          <div className="flex flex-wrap gap-2">
            {keywords.map((kw: any, i: number) => {
              const size = Math.max(0.75, Math.min(2, kw.score / 10));
              return (
                <span key={i} className="px-3 py-1 rounded-full text-sm border"
                  style={{
                    fontSize: `${size}rem`,
                    borderColor: `hsl(${240 + i * 20}, 70%, 75%)`,
                    backgroundColor: `hsl(${240 + i * 20}, 70%, 95%)`,
                  }}>
                  {kw.word}
                  <span className="text-xs text-gray-400 ml-1">{kw.frequency}</span>
                </span>
              );
            })}
          </div>
        </div>
      )}

      {/* Themes */}
      {themes.length > 0 && (
        <div>
          <h4 className="font-semibold text-gray-700 mb-3">需求主题聚类</h4>
          <div className="grid grid-cols-2 gap-4">
            {themes.map((theme: any, i: number) => (
              <div key={i} className="border border-gray-100 rounded-xl p-4">
                <div className="flex items-center justify-between mb-2">
                  <div className="font-medium text-gray-800">{theme.theme}</div>
                  <span className="text-xs px-2 py-0.5 bg-indigo-100 text-indigo-700 rounded-full">
                    权重 {Math.round(theme.weight * 100)}%
                  </span>
                </div>
                <div className="flex flex-wrap gap-1 mb-2">
                  {(theme.keywords || []).slice(0, 5).map((kw: string, j: number) => (
                    <span key={j} className="text-xs px-2 py-0.5 bg-gray-100 rounded-full text-gray-600">{kw}</span>
                  ))}
                </div>
                {(theme.representative_quotes || []).length > 0 && (
                  <div className="text-xs text-gray-400 space-y-1">
                    {(theme.representative_quotes || []).map((q: string, j: number) => (
                      <div key={j} className="border-l-2 border-gray-200 pl-2 italic">"{q.slice(0, 100)}"</div>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function InsightsPanel({ results, taskId }: { results: AnalysisResults; taskId?: string }) {
  const insights = results.insights || [];
  const aiInsights = (results as any).ai_insights || [];
  const report = results.report;

  const typeLabels: Record<string, string> = {
    trend: "趋势", anomaly: "异常", correlation: "相关性", segmentation: "分群",
  };

  // Recommendations from report or AI insights
  const recommendations = report?.recommendations || aiInsights;

  return (
    <div className="space-y-6">
      {insights.length === 0 && aiInsights.length === 0 && (
        <div className="text-gray-400 text-center py-8">暂无洞察数据</div>)}

      {/* Numerical insights */}
      {insights.map((ins, idx) => (
        <div key={idx} className="border border-gray-100 rounded-xl p-4 hover:border-gray-200 transition-colors">
          <div className="flex items-center gap-2 mb-2">
            <span className={`text-xs px-2 py-0.5 rounded-full ${
              ins.type === "trend" ? "bg-blue-100 text-blue-700" :
              ins.type === "anomaly" ? "bg-red-100 text-red-700" :
              ins.type === "correlation" ? "bg-purple-100 text-purple-700" :
              "bg-green-100 text-green-700"
            }`}>
              {typeLabels[ins.type] || ins.type}
            </span>
            <span className="text-xs text-gray-400">重要性: {(ins.importance_score * 100).toFixed(0)}%</span>
            <span className="text-xs text-gray-400">置信度: {(ins.confidence * 100).toFixed(0)}%</span>
          </div>
          <h4 className="font-medium text-gray-800">{ins.title}</h4>
          <p className="text-sm text-gray-500 mt-1">{ins.description}</p>
        </div>
      ))}

      {/* AI insights (content analysis) */}
      {aiInsights.length > 0 && (
        <div>
          <h4 className="font-semibold text-gray-700 mb-3">🤖 AI 深度洞察</h4>
          <div className="space-y-3">
            {aiInsights.map((rec: any, idx: number) => (
              <div key={idx} className="bg-indigo-50 border border-indigo-100 rounded-xl p-4">
                <div className="font-medium text-[#4f46e5]">{rec.title}</div>
                <div className="text-sm text-gray-600 mt-1">{rec.detail}</div>
                {rec.action && (
                  <div className="text-sm text-[#6366f1] mt-2 bg-white rounded-lg px-3 py-2">➤ {rec.action}</div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Recommendations from report */}
      {recommendations && recommendations.length > 0 && !aiInsights.length && (
        <div>
          <h4 className="font-semibold text-gray-700 mb-3">行动建议</h4>
          <div className="space-y-3">
            {recommendations.map((rec: any, idx: number) => (
              <div key={idx} className="bg-indigo-50 border border-indigo-100 rounded-xl p-4">
                <div className="font-medium text-[#4f46e5]">{rec.title}</div>
                <div className="text-sm text-gray-600 mt-1">{rec.detail}</div>
                {rec.action && (
                  <div className="text-sm text-[#6366f1] mt-2 bg-white rounded-lg px-3 py-2">{rec.action}</div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
