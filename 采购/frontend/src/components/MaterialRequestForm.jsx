import React, { useMemo, useState, useRef } from "react";
import { api } from "../api/http";
import { useAuth } from "../auth/AuthContext";
import { ENDPOINTS } from "../api/endpoints";

// 收货地点配置
const DELIVERY_LOCATIONS = [
  { value: "东莞工厂 - 水边工业园", label: "🏭 东莞工厂 - 水边工业园" },
  { value: "深圳工厂 - 东森工业园", label: "🏭 深圳工厂 - 东森工业园" },
];

const emptyRow = () => ({
  name: "",
  spec: "",
  qty: 1,
  unit: "件",
  remark: "",
  needDate: new Date().toISOString().split("T")[0],
  deliverTo: "东莞工厂 - 水边工业园",
  logisticsNote: "",
});

export default function MaterialRequestForm() {
  const { user } = useAuth();

  const PAGE_TITLE = "物料申请单";
  const [formTitle, setFormTitle] = useState("");
  const [items, setItems] = useState([emptyRow()]);
  const [submitting, setSubmitting] = useState(false);
  const [msg, setMsg] = useState({ ok: "", err: "" });
  const [urgency, setUrgency] = useState("medium");

  const [searchResults, setSearchResults] = useState({});
  const [activeDropdown, setActiveDropdown] = useState(null);
  const [searchLoading, setSearchLoading] = useState({});
  const searchTimeoutRef = useRef({});

  const totalQty = useMemo(
    () => items.reduce((s, r) => s + (Number(r.qty) || 0), 0),
    [items]
  );

  const searchMaterials = async (idx, query) => {
    if (!query.trim()) {
      setSearchResults((s) => ({ ...s, [idx]: [] }));
      return;
    }

    setSearchLoading((s) => ({ ...s, [idx]: true }));
    try {
      const res = await api.get(ENDPOINTS.PR.SEARCH_MATERIALS(query));
      const materials = res?.data || [];

      const grouped = {};
      materials.forEach((item) => {
        const name = item.name.trim();
        const spec = item.spec || "";
        
        if (!grouped[name]) {
          grouped[name] = { name, specs: [] };
        }
        
        if (spec && !grouped[name].specs.includes(spec)) {
          grouped[name].specs.push(spec);
        }
      });

      setSearchResults((s) => ({ ...s, [idx]: grouped }));
    } catch (e) {
      console.error("搜索物料失败:", e);
      setSearchResults((s) => ({ ...s, [idx]: [] }));
    } finally {
      setSearchLoading((s) => ({ ...s, [idx]: false }));
    }
  };

  const handleMaterialSearch = (idx, query) => {
    update(idx, "name", query);
    clearTimeout(searchTimeoutRef.current[idx]);
    searchTimeoutRef.current[idx] = setTimeout(() => {
      searchMaterials(idx, query);
    }, 300);
  };

  const selectMaterial = (idx, materialName, spec) => {
    update(idx, "name", materialName);
    update(idx, "spec", spec);
    setActiveDropdown(null);
    setSearchResults((s) => ({ ...s, [idx]: [] }));
  };

  const addRow = () => setItems((s) => [...s, emptyRow()]);
  const removeRow = (idx) =>
    setItems((s) => (s.length > 1 ? s.filter((_, i) => i !== idx) : s));
  const copyRow = (idx) => {
    const newItem = { ...items[idx], qty: 1 };
    setItems((s) => [...s, newItem]);
  };
  const update = (idx, k, v) =>
    setItems((s) => s.map((r, i) => (i === idx ? { ...r, [k]: v } : r)));

  const submit = async () => {
    setMsg({ ok: "", err: "" });
    try {
      if (!items.length) throw new Error("请至少添加一行物料");
      for (const [i, r] of items.entries()) {
        if (!r.name?.trim()) throw new Error(`第 ${i + 1} 行：物料名称必填`);
        if (!r.qty || Number(r.qty) <= 0) throw new Error(`第 ${i + 1} 行：数量需大于 0`);
      }
      if (!user?.id) throw new Error("未获取到当前用户，请先登录后再试");

      setSubmitting(true);

      const head = items[0] || {};
      const description = [
        `需求到货日: ${head.needDate || ""}`,
        `收货地: ${head.deliverTo || ""}`,
        `物流备注: ${head.logisticsNote || ""}`,
      ]
        .filter(Boolean)
        .join(" | ");

      const payload = {
        title: (formTitle || PAGE_TITLE).trim(),
        description,
        urgency,
        owner_id: user.id,
        items: items.map((r) => ({
          name: r.name?.trim(),
          spec: r.spec || "",
          qty: Number(r.qty) || 1,
          unit: r.unit || "件",
          remark: r.remark || "",
        })),
      };

      const res = await api.post(ENDPOINTS.PR.CREATE, payload);
      const prNo = res?.prNumber || res?.data?.prNumber || res?.pr_number;

      setMsg({ ok: `✅ 提交成功${prNo ? `，单号：${prNo}` : ""}`, err: "" });
      setItems([emptyRow()]);
      setUrgency("medium");
      setFormTitle("");
    } catch (e) {
      setMsg({ ok: "", err: e.message || String(e) });
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-slate-100 p-4 md:p-8">
      <div className="max-w-6xl mx-auto">
        
        {/* 页面头部 */}
        <div className="mb-6">
          <h1 className="text-2xl md:text-4xl font-bold text-slate-900 mb-2 flex items-center gap-2 md:gap-3">
            <div className="w-10 h-10 md:w-12 md:h-12 bg-gradient-to-br from-blue-500 to-blue-600 rounded-lg flex items-center justify-center text-white text-base md:text-lg font-bold">
              📋
            </div>
            {PAGE_TITLE}
          </h1>
          <p className="text-sm md:text-base text-slate-500">快速、高效的物料申请流程</p>
        </div>

        {/* 消息提示 */}
        {msg.ok && (
          <div className="mb-4 p-4 bg-green-50 border border-green-200 text-green-700 rounded-lg flex items-center gap-2">
            <span className="text-xl">✓</span>
            {msg.ok}
          </div>
        )}
        {msg.err && (
          <div className="mb-4 p-4 bg-red-50 border border-red-200 text-red-700 rounded-lg flex items-center gap-2">
            <span className="text-xl">⚠️</span>
            {msg.err}
          </div>
        )}

        {/* 基本信息 + 物流信息（合并为一个卡片）*/}
        <div className="bg-white rounded-2xl shadow-sm border border-slate-100 p-6 md:p-8 mb-3">
          <h2 className="text-base font-semibold text-slate-900 mb-3">基本信息 & 物流信息</h2>

          <div className="space-y-3">
            {/* 申请标题 */}
            <div>
              <label className="block text-xs font-medium text-slate-600 mb-1.5">
                申请标题 <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                placeholder="如：刀具采购—项目A"
                value={formTitle}
                onChange={(e) => setFormTitle(e.target.value)}
                disabled={submitting}
                className="w-full px-3 py-2 text-sm border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition"
              />
            </div>

            {/* 基本信息和物流信息横向排列 */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              {/* 申请人 */}
              <div>
                <label className="block text-xs font-medium text-slate-600 mb-1.5">申请人</label>
                <div className="flex items-center px-3 py-2 text-sm bg-slate-50 border border-slate-200 rounded-lg">
                  <span className="text-sm mr-1.5">👤</span>
                  <span className="text-slate-700 font-medium">{user?.full_name || user?.name || user?.username || "未登录"}</span>
                </div>
              </div>

              {/* 申请部门 */}
              <div>
                <label className="block text-xs font-medium text-slate-600 mb-1.5">申请部门</label>
                <div className="flex items-center px-3 py-2 text-sm bg-slate-50 border border-slate-200 rounded-lg">
                  <span className="text-sm mr-1.5">🏢</span>
                  <span className="text-slate-700 font-medium">{user?.department_name || user?.department || "未设置"}</span>
                </div>
              </div>

              {/* 紧急程度 */}
              <div>
                <label className="block text-xs font-medium text-slate-600 mb-1.5">紧急程度</label>
                <select
                  value={urgency}
                  onChange={(e) => setUrgency(e.target.value)}
                  disabled={submitting}
                  className="w-full px-3 py-2 text-sm border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <option value="low">🔵 低</option>
                  <option value="medium">🟡 中</option>
                  <option value="high">🔴 高</option>
                </select>
              </div>

              {/* 需求到货日 */}
              <div>
                <label className="block text-xs font-medium text-slate-600 mb-1.5">需求到货日</label>
                <input
                  type="date"
                  value={items[0]?.needDate || ""}
                  onChange={(e) => update(0, "needDate", e.target.value)}
                  disabled={submitting}
                  className="w-full px-3 py-2 text-sm border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>

              {/* 收货地点 */}
              <div>
                <label className="block text-xs font-medium text-slate-600 mb-1.5">收货地点</label>
                <select
                  value={items[0]?.deliverTo || ""}
                  onChange={(e) => update(0, "deliverTo", e.target.value)}
                  disabled={submitting}
                  className="w-full px-3 py-2 text-sm border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  {DELIVERY_LOCATIONS.map((location) => (
                    <option key={location.value} value={location.value}>
                      {location.label}
                    </option>
                  ))}
                </select>
              </div>

              {/* 物流备注 */}
              <div>
                <label className="block text-xs font-medium text-slate-600 mb-1.5">物流备注</label>
                <input
                  type="text"
                  placeholder="特殊要求等"
                  value={items[0]?.logisticsNote || ""}
                  onChange={(e) => update(0, "logisticsNote", e.target.value)}
                  disabled={submitting}
                  className="w-full px-3 py-2 text-sm border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
            </div>
          </div>
        </div>

        {/* 物料明细卡片 */}
        <div className="bg-white rounded-2xl shadow-sm border border-slate-100 p-6 md:p-8 mb-3">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-base font-semibold text-slate-900">物料明细</h2>
            <div className="text-xs font-semibold text-blue-600 bg-blue-50 px-3 py-1.5 rounded-full">
              📦 共 {items.length} 项 | 合计 {totalQty} 件
            </div>
          </div>

          <div className="space-y-3">
            {items.map((r, idx) => (
              <div key={idx} className="border border-slate-200 rounded-lg p-3 bg-slate-50 hover:bg-slate-100/50 transition">
                {/* 手机端：序号和删除按钮在顶部 */}
                <div className="flex items-center justify-between mb-2 md:hidden">
                  <div className="text-sm font-bold text-blue-600 bg-blue-50 px-2 py-1 rounded">
                    第 {idx + 1} 项
                  </div>
                  {items.length > 1 && (
                    <button
                      type="button"
                      onClick={() => removeRow(idx)}
                      disabled={submitting}
                      className="text-xs text-red-500 hover:text-red-700"
                    >
                      删除
                    </button>
                  )}
                </div>

                {/* 桌面端：12列网格 / 手机端：堆叠布局 */}
                <div className="grid grid-cols-2 md:grid-cols-12 gap-2 items-end">
                  {/* 序号 - 仅桌面端显示 */}
                  <div className="hidden md:block md:col-span-1">
                    <label className="text-xs text-slate-500 font-semibold mb-1 block">序号</label>
                    <div className="text-lg font-bold text-blue-600">{idx + 1}</div>
                  </div>

                  {/* 物料名称 */}
                  <div className="col-span-2 md:col-span-3 relative">
                    <label className="text-xs text-slate-500 font-semibold mb-1 block">物料名称 *</label>
                    <div className="relative">
                      <span className="absolute left-2.5 top-2.5 text-slate-400 text-sm">🔍</span>
                      <input
                        type="text"
                        placeholder="输入搜索..."
                        value={r.name}
                        onChange={(e) => handleMaterialSearch(idx, e.target.value)}
                        onFocus={() => r.name && setActiveDropdown(idx)}
                        disabled={submitting}
                        autoComplete="off"
                        className="w-full pl-8 pr-3 py-2 text-sm border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      />

                      {/* 搜索下拉 */}
                      {activeDropdown === idx && Object.keys(searchResults[idx] || {}).length > 0 && (
                        <div className="absolute top-full left-0 right-0 bg-white border border-slate-200 rounded-lg shadow-lg z-10 mt-1 max-h-48 overflow-y-auto">
                          {Object.entries(searchResults[idx]).map(([materialName, { specs }]) => (
                            <div key={materialName}>
                              {specs.map((spec, specIdx) => (
                                <button
                                  key={`${materialName}-${specIdx}`}
                                  type="button"
                                  className="w-full px-3 py-1.5 text-left hover:bg-blue-50 border-b border-slate-100 last:border-b-0 transition text-sm"
                                  onClick={() => selectMaterial(idx, materialName, spec)}
                                >
                                  <div className="font-medium text-slate-900">{materialName}</div>
                                  <div className="text-xs text-slate-500">{spec}</div>
                                </button>
                              ))}
                            </div>
                          ))}
                        </div>
                      )}

                      {searchLoading[idx] && (
                        <span className="absolute right-2.5 top-2.5 text-blue-500 animate-spin text-sm">⏳</span>
                      )}
                    </div>
                  </div>

                  {/* 规格 */}
                  <div className="col-span-2 md:col-span-2">
                    <label className="text-xs text-slate-500 font-semibold mb-1 block">规格/型号</label>
                    <input
                      type="text"
                      placeholder="自动填充"
                      value={r.spec}
                      onChange={(e) => update(idx, "spec", e.target.value)}
                      disabled={submitting}
                      className="w-full px-3 py-2 text-sm border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                  </div>

                  {/* 数量 */}
                  <div className="col-span-1 md:col-span-1">
                    <label className="text-xs text-slate-500 font-semibold mb-1 block">数量 *</label>
                    <input
                      type="number"
                      min={1}
                      value={r.qty}
                      onChange={(e) => update(idx, "qty", Number(e.target.value || 1))}
                      disabled={submitting}
                      className="w-full px-3 py-2 text-sm border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                  </div>

                  {/* 单位 */}
                  <div className="col-span-1 md:col-span-1">
                    <label className="text-xs text-slate-500 font-semibold mb-1 block">单位</label>
                    <input
                      type="text"
                      placeholder="件"
                      value={r.unit}
                      onChange={(e) => update(idx, "unit", e.target.value)}
                      disabled={submitting}
                      className="w-full px-3 py-2 text-sm border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                  </div>

                  {/* 备注 */}
                  <div className="col-span-2 md:col-span-3">
                    <label className="text-xs text-slate-500 font-semibold mb-1 block">备注</label>
                    <input
                      type="text"
                      placeholder="如有特殊要求..."
                      value={r.remark}
                      onChange={(e) => update(idx, "remark", e.target.value)}
                      disabled={submitting}
                      className="w-full px-3 py-2 text-sm border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                  </div>
                </div>

                {/* 操作按钮 - 最后一行显示 */}
                {idx === items.length - 1 && (
                  <div className="flex flex-wrap gap-2 mt-3 pt-3 border-t border-slate-200">
                    <button
                      type="button"
                      onClick={() => copyRow(idx)}
                      disabled={submitting}
                      className="flex-1 md:flex-none flex items-center justify-center gap-1.5 px-3 py-2 text-xs font-medium text-slate-700 bg-slate-100 hover:bg-slate-200 rounded-lg disabled:opacity-50 transition"
                    >
                      📋 复制
                    </button>
                    <button
                      type="button"
                      onClick={addRow}
                      disabled={submitting}
                      className="flex-1 md:flex-none flex items-center justify-center gap-1.5 px-3 py-2 text-xs font-medium text-white bg-green-500 hover:bg-green-600 rounded-lg disabled:opacity-50 transition"
                    >
                      ➕ 新增
                    </button>
                    {items.length > 1 && (
                      <button
                        type="button"
                        onClick={() => removeRow(idx)}
                        disabled={submitting}
                        className="hidden md:flex items-center gap-1.5 px-3 py-2 text-xs font-medium text-white bg-red-500 hover:bg-red-600 rounded-lg disabled:opacity-50 transition ml-auto"
                      >
                        🗑️ 删除
                      </button>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* 提交按钮 */}
        <div className="flex flex-col md:flex-row justify-end gap-3 mt-4">
          <button
            type="button"
            onClick={() => {
              setItems([emptyRow()]);
              setFormTitle("");
              setUrgency("medium");
            }}
            disabled={submitting}
            className="w-full md:w-auto px-6 py-3 border border-slate-300 text-slate-700 font-semibold rounded-lg hover:bg-slate-50 disabled:opacity-50 transition"
          >
            重置
          </button>
          <button
            type="button"
            onClick={submit}
            disabled={submitting}
            className="w-full md:w-auto px-8 py-3 bg-gradient-to-r from-blue-500 to-blue-600 text-white font-semibold rounded-lg hover:from-blue-600 hover:to-blue-700 disabled:opacity-50 transition flex items-center justify-center gap-2"
          >
            {submitting ? (
              <>
                <span className="animate-spin">⏳</span>
                提交中...
              </>
            ) : (
              <>
                ✓ 提交申请
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}