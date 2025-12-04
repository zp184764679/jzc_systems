// src/components/PrAiAssist.jsx
import React, { useRef, useState } from "react";
import { ENDPOINTS } from "../api/endpoints"

/**
 * Props:
 * - title: string
 * - onTitleChange: (v: string) => void
 * - items: any[]                           // 用于"智能补全"把当前行发给后端
 * - onMerge: (aiItems: any[]) => void      // 合并到现有行（父组件决定如何 merge）
 * - onReplace: (fixedItems: any[]) => void // 用 AI 结果整体替换（用于 complete）
 *
 * 后端端点从 endpoints.js 导入：
 *  POST /api/ai/pr/suggest-items { title }          -> { items: [...] }
 *  POST /api/ai/pr/complete      { items }          -> { items: [...] }
 *  POST /api/ai/pr/ocr           (multipart: file)  -> { items: [...], title? }
 *  GET  /api/ai/pr/history?title=...                -> { items: [...] }
 */
export default function PrAiAssist({
  title,
  onTitleChange,
  items,
  onMerge,
  onReplace,
}) {
  const [aiLoading, setAiLoading] = useState(false);
  const [aiMsg, setAiMsg] = useState({ ok: "", err: "" });
  const fileRef = useRef(null);

  const withBusy = async (fn) => {
    setAiMsg({ ok: "", err: "" });
    try {
      setAiLoading(true);
      await fn();
    } catch (e) {
      setAiMsg({ ok: "", err: e?.message || String(e) });
    } finally {
      setAiLoading(false);
    }
  };

  const fromTitle = () =>
    withBusy(async () => {
      if (!title?.trim()) throw new Error('请先填写 "申请标题/用途"');
      const r = await fetch(ENDPOINTS.AI.SUGGEST_ITEMS, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title }),
      });
      const data = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(data?.error || `HTTP ${r.status}`);
      const aiItems = Array.isArray(data.items) ? data.items : [];
      if (!aiItems.length) throw new Error("AI 未返回可用物料建议");
      onMerge?.(aiItems);
      setAiMsg({ ok: `已根据标题添加/合并 ${aiItems.length} 条物料`, err: "" });
    });

  const completeRows = () =>
    withBusy(async () => {
      const r = await fetch(ENDPOINTS.AI.COMPLETE_ITEMS, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ items }),
      });
      const data = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(data?.error || `HTTP ${r.status}`);
      const fixed = Array.isArray(data.items) ? data.items : [];
      if (fixed.length) onReplace?.(fixed);
      setAiMsg({ ok: "已对当前明细进行规范化与补全", err: "" });
    });

  const fromHistory = () =>
    withBusy(async () => {
      const endpoint = ENDPOINTS.AI.GET_HISTORY(title);
      const r = await fetch(endpoint);
      const data = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(data?.error || `HTTP ${r.status}`);
      const aiItems = Array.isArray(data.items) ? data.items : [];
      if (!aiItems.length) throw new Error("暂无历史推荐");
      onMerge?.(aiItems);
      setAiMsg({ ok: `已从历史 PR 合并 ${aiItems.length} 条物料`, err: "" });
    });

  const onFile = (file) =>
    withBusy(async () => {
      if (!file) return;
      const fd = new FormData();
      fd.append("file", file);
      const r = await fetch(ENDPOINTS.AI.OCR, { method: "POST", body: fd });
      const data = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(data?.error || `HTTP ${r.status}`);
      const aiItems = Array.isArray(data.items) ? data.items : [];
      if (data.title && !title) onTitleChange?.(data.title);
      if (aiItems.length) onMerge?.(aiItems);
      setAiMsg({ ok: `OCR 识别完成，合并 ${aiItems.length} 条物料`, err: "" });
      if (fileRef.current) fileRef.current.value = "";
    });

  return (
    <div className="rounded-xl border p-4 space-y-3 bg-white">
      <div className="flex items-center justify-between">
        <div className="font-semibold">AI 助填</div>
        {aiLoading && (
          <div className="text-xs text-gray-500 animate-pulse">AI 处理中…</div>
        )}
      </div>

      {aiMsg.err && (
        <div className="p-2 rounded border border-red-300 bg-red-50 text-red-700 text-xs">
          {aiMsg.err}
        </div>
      )}
      {aiMsg.ok && (
        <div className="p-2 rounded border border-green-300 bg-green-50 text-green-700 text-xs">
          {aiMsg.ok}
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-12 gap-2">
        <button
          type="button"
          className="md:col-span-3 px-3 py-2 border rounded hover:bg-gray-50"
          onClick={fromTitle}
          disabled={aiLoading}
          title="根据标题联想常见物料（本地大模型 + 规则库）"
        >
          从标题联想物料
        </button>

        <button
          type="button"
          className="md:col-span-3 px-3 py-2 border rounded hover:bg-gray-50"
          onClick={completeRows}
          disabled={aiLoading}
          title="对当前明细进行单位/规格/数量的规范化与补全"
        >
          智能补全当前行
        </button>

        <button
          type="button"
          className="md:col-span-3 px-3 py-2 border rounded hover:bg-gray-50"
          onClick={fromHistory}
          disabled={aiLoading}
          title="基于历史 PR 与相似标题快速组装常买清单"
        >
          从历史 PR 推荐
        </button>

        <label className="md:col-span-3 px-3 py-2 border rounded hover:bg-gray-50 cursor-pointer text-center">
          识别纸质申请单（OCR）
          <input
            ref={fileRef}
            type="file"
            accept="image/*,application/pdf"
            className="hidden"
            onChange={(e) => onFile(e.target.files?.[0])}
          />
        </label>
      </div>

      <div className="text-xs text-gray-500">
        后端将本地大模型接到 <code className="px-1">/api/ai/pr/*</code> 端点；模型输出先经规则/词典结构化再返回。
      </div>
    </div>
  );
}