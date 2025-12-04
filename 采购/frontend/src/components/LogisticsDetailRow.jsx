// src/components/LogisticsDetailRow.jsx
// 说明：仅负责 PR 行内的“物流明细”字段渲染与回写；不包含任何金额/供应商逻辑
import React from "react";

export default function LogisticsDetailRow({
  row,
  onChange,          // (key, value) => void
  className = "",
}) {
  const update = (k) => (e) => onChange(k, e.target.value);

  return (
    <div className={`md:col-span-12 grid grid-cols-1 md:grid-cols-12 gap-2 ${className}`}>
      <div className="md:col-span-2">
        <label className="text-xs text-gray-500">行-需求到货日</label>
        <input
          type="date"
          className="border p-2 rounded w-full"
          value={row.needDate || ""}
          onChange={update("needDate")}
        />
      </div>

      <div className="md:col-span-2">
        <label className="text-xs text-gray-500">包装方式</label>
        <select
          className="border p-2 rounded w-full"
          value={row.packageType || ""}
          onChange={update("packageType")}
        >
          <option value="">请选择</option>
          <option value="carton">纸箱</option>
          <option value="wood">木箱</option>
          <option value="pallet">托盘</option>
          <option value="bulk">散装</option>
        </select>
      </div>

      <div className="md:col-span-2">
        <label className="text-xs text-gray-500">运输方式</label>
        <select
          className="border p-2 rounded w-full"
          value={row.shipMethod || ""}
          onChange={update("shipMethod")}
        >
          <option value="">请选择</option>
          <option value="express">快递</option>
          <option value="logistics">物流</option>
          <option value="pickup">自提</option>
        </select>
      </div>

      <div className="md:col-span-3">
        <label className="text-xs text-gray-500">收货地 / 交付地点</label>
        <input
          className="border p-2 rounded w-full"
          placeholder="如：一厂A库 / 二厂收料口"
          value={row.deliverTo || ""}
          onChange={update("deliverTo")}
        />
      </div>

      <div className="md:col-span-3">
        <label className="text-xs text-gray-500">物流备注（行）</label>
        <input
          className="border p-2 rounded w-full"
          placeholder="如：含卸货、需上楼、白天送达"
          value={row.logisticsNote || ""}
          onChange={update("logisticsNote")}
        />
      </div>
    </div>
  );
}
