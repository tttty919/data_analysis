"use client";
import type { AnalysisResults } from "@/lib/types";

function Card({ label, value }: { label: string; value: string }) {
  return (
    <div className="bg-gray-50 rounded-xl p-4 text-center">
      <div className="text-2xl font-bold text-[#6366f1]">{value}</div>
      <div className="text-xs text-gray-400 mt-1">{label}</div>
    </div>
  );
}

/* ====== NPS Panel ====== */

export function NPSPanel({ results }: { results: AnalysisResults }) {
  const nps = (results as any).nps;
  if (!nps) return <div className="text-gray-400 text-center py-8">暂无NPS数据</div>;
  const sc = nps.nps_score >= 50 ? "text-green-500" : nps.nps_score >= 0 ? "text-yellow-500" : "text-red-500";
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-3 gap-4">
        <div className="bg-gray-50 rounded-xl p-6 text-center">
          <div className={`text-5xl font-bold ${sc}`}>{nps.nps_score}</div>
          <div className="text-sm text-gray-400 mt-2">NPS得分</div>
          <div className="text-xs text-gray-500">{nps.level}</div>
        </div>
        <div className="bg-green-50 rounded-xl p-4 text-center">
          <div className="text-2xl font-bold text-green-600">{nps.promoters_pct}%</div>
          <div className="text-xs text-gray-500 mt-1">推荐者 Promoters</div>
        </div>
        <div className="bg-red-50 rounded-xl p-4 text-center">
          <div className="text-2xl font-bold text-red-600">{nps.detractors_pct}%</div>
          <div className="text-xs text-gray-500 mt-1">贬损者 Detractors</div>
        </div>
      </div>
      <div className="flex h-10 rounded-full overflow-hidden text-xs">
        <div style={{ width: `${nps.detractors_pct}%` }} className="bg-red-400 flex items-center justify-center text-white">贬损{nps.detractors_pct}%</div>
        <div style={{ width: `${nps.passives_pct}%` }} className="bg-yellow-300 flex items-center justify-center text-yellow-800">被动{nps.passives_pct}%</div>
        <div style={{ width: `${nps.promoters_pct}%` }} className="bg-green-400 flex items-center justify-center text-white">推荐{nps.promoters_pct}%</div>
      </div>
      <div className="text-xs text-gray-400">受访{nps.total_respondents}人 · {nps.benchmark}</div>
    </div>
  );
}

/* ====== Pain Points Panel ====== */

export function PainPointsPanel({ results }: { results: AnalysisResults }) {
  const pp = (results as any).pain_points || [];
  if (!pp.length) return <div className="text-gray-400 text-center py-8">暂无痛点数据</div>;
  return (
    <div className="space-y-4">
      <h4 className="font-semibold text-gray-700">痛点评级矩阵</h4>
      <p className="text-xs text-gray-400">按 频率 × 严重度 排序，P0 优先处理</p>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-gray-50">
              <th className="text-left p-2 font-medium text-gray-500">优先级</th>
              <th className="text-left p-2 font-medium text-gray-500">痛点</th>
              <th className="text-right p-2 font-medium text-gray-500">提及</th>
              <th className="text-right p-2 font-medium text-gray-500">严重度</th>
              <th className="text-right p-2 font-medium text-gray-500">影响分</th>
            </tr>
          </thead>
          <tbody>
            {pp.map((p: any, i: number) => (
              <tr key={i} className={`border-t border-gray-50 ${(p.priority || "").includes("P0") ? "bg-red-50" : ""}`}>
                <td className="p-2">
                  <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                    (p.priority || "").includes("P0") ? "bg-red-100 text-red-700" :
                    (p.priority || "").includes("P1") ? "bg-orange-100 text-orange-700" :
                    "bg-gray-100 text-gray-600"
                  }`}>{p.priority}</span>
                </td>
                <td className="p-2 font-medium">{p.pain_point}</td>
                <td className="text-right p-2">{p.mention_count || p.frequency}</td>
                <td className="text-right p-2">{((p.severity_score || 0) * 100).toFixed(0)}%</td>
                <td className="text-right p-2 font-medium">{((p.impact_score || 0) * 100).toFixed(0)}%</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

/* ====== Competitor Panel ====== */

export function CompetitorPanel({ results }: { results: AnalysisResults }) {
  const cd = (results as any).competitor_mentions;
  const details = cd?.details || [];
  if (!details.length) return <div className="text-gray-400 text-center py-8">未检测到竞品提及</div>;
  return (
    <div className="space-y-4">
      <div className="flex gap-4">
        <Card label="提及总数" value={String(cd.total_mentions)} />
        <Card label="涉及竞品" value={String(cd.competitors_found)} />
      </div>
      {details.map((c: any, i: number) => (
        <div key={i} className="border border-gray-100 rounded-xl p-4">
          <div className="flex items-center justify-between mb-2">
            <div className="font-medium text-gray-800">{c.brand}</div>
            <span className="text-xs text-gray-400">提及{c.mention_count}次 ({c.mention_rate}%)</span>
          </div>
          {c.sample_quotes?.length > 0 && (
            <div className="text-xs text-gray-400 space-y-1">
              {c.sample_quotes.map((q: string, j: number) => (
                <div key={j} className="border-l-2 border-gray-200 pl-2">"{q.slice(0, 150)}"</div>
              ))}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}

/* ====== User Segments Panel ====== */

export function SegmentsPanel({ results }: { results: AnalysisResults }) {
  const segs = (results as any).user_segments || [];
  if (!segs.length) return <div className="text-gray-400 text-center py-8">暂无分群数据</div>;
  const colors = ["border-l-indigo-500", "border-l-red-500", "border-l-yellow-500", "border-l-green-500"];
  return (
    <div className="space-y-4">
      <h4 className="font-semibold text-gray-700">用户分群画像</h4>
      {segs.map((s: any, i: number) => (
        <div key={i} className={`border border-gray-100 rounded-xl p-5 border-l-4 ${colors[i % 4]}`}>
          <div className="flex items-center justify-between mb-3">
            <h5 className="font-semibold text-gray-800">{s.segment_name}</h5>
            <span className="bg-gray-100 text-gray-600 text-xs px-3 py-1 rounded-full">{s.count}人 ({s.percentage}%)</span>
          </div>
          <div className="text-sm text-gray-600 space-y-2">
            <div><span className="text-gray-400">画像：</span>{s.profile}</div>
            <div><span className="text-gray-400">需求：</span>{s.needs}</div>
            <div><span className="text-gray-400">风险：</span>{s.risk}</div>
          </div>
          {s.sample_users?.length > 0 && (
            <div className="mt-2 text-xs text-gray-400">示例：{s.sample_users.slice(0, 5).join("、")}</div>
          )}
        </div>
      ))}
    </div>
  );
}

/* ====== JTBD Panel ====== */

export function JTBDPanel({ results }: { results: AnalysisResults }) {
  const jt = (results as any).jtbd || [];
  if (!jt.length) return <div className="text-gray-400 text-center py-8">暂无JTBD数据</div>;
  return (
    <div className="space-y-4">
      <h4 className="font-semibold text-gray-700">Jobs-to-be-Done</h4>
      <p className="text-xs text-gray-400">用户"雇佣"产品完成的任务（功能性 + 情感性）</p>
      <div className="grid grid-cols-2 gap-4">
        {jt.map((j: any, i: number) => (
          <div key={i} className="border border-gray-100 rounded-xl p-4 hover:border-indigo-200 transition-colors">
            <div className="flex items-center justify-between mb-2">
              <h5 className="font-semibold text-gray-800">{j.job_name}</h5>
              <span className="text-xs text-gray-400">{j.mention_rate}%</span>
            </div>
            <div className="text-sm space-y-2">
              <div>
                <span className="text-xs text-indigo-400 font-medium">功能性任务</span>
                <p className="text-gray-600 mt-0.5">{j.functional_job}</p>
              </div>
              <div>
                <span className="text-xs text-purple-400 font-medium">情感性任务</span>
                <p className="text-gray-600 mt-0.5">{j.emotional_job}</p>
              </div>
            </div>
            <div className="flex flex-wrap gap-1 mt-3">
              {(j.keywords_matched || []).map((k: string, ji: number) => (
                <span key={ji} className="text-xs px-2 py-0.5 bg-gray-100 rounded-full text-gray-500">{k}</span>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

/* ====== Customer Journey Panel ====== */

export function JourneyPanel({ results }: { results: AnalysisResults }) {
  const jn = (results as any).customer_journey;
  if (!jn?.stages?.length) return <div className="text-gray-400 text-center py-8">暂无旅程数据</div>;
  return (
    <div className="space-y-6">
      <div>
        <h4 className="font-semibold text-gray-700 mb-1">用户旅程情感曲线</h4>
        <p className="text-sm text-gray-500">{jn.insight}</p>
      </div>
      <div className="relative">
        <div className="flex items-end gap-4 h-48 mb-2">
          {jn.stages.map((s: any, i: number) => {
            const h = Math.abs(s.sentiment_score) * 150 + 20;
            const p = s.sentiment_score >= 0;
            return (
              <div key={i} className="flex-1 flex flex-col items-center justify-end h-full">
                <div className="text-xs mb-1">{p ? "😊" : s.sentiment_score < -0.2 ? "😟" : "😐"}</div>
                <div style={{ height: `${h}px` }}
                  className={`w-full max-w-[60px] rounded-t-lg ${p ? "bg-green-400" : s.sentiment_score < -0.2 ? "bg-red-400" : "bg-gray-300"}`} />
              </div>
            );
          })}
        </div>
        <div className="flex gap-4">
          {jn.stages.map((s: any, i: number) => (
            <div key={i} className="flex-1 text-center">
              <div className="text-xs font-medium text-gray-700">{s.stage}</div>
              <div className="text-xs text-gray-400">{s.mention_count}条</div>
              <div className={`text-xs ${s.sentiment_score >= 0 ? "text-green-500" : "text-red-500"}`}>{s.sentiment_label}</div>
            </div>
          ))}
        </div>
      </div>
      {jn.stages.filter((s: any) => s.sample_quote).map((s: any, i: number) => (
        <div key={i} className="border border-gray-100 rounded-lg p-3">
          <div className="text-xs font-medium text-gray-500 mb-1">{s.stage}</div>
          <div className="text-sm text-gray-600">"{s.sample_quote}"</div>
        </div>
      ))}
    </div>
  );
}
