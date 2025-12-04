import React, { useState } from "react";

/**
 * FilterBar - 筛选条组件
 * 提供搜索、状态筛选、紧急程度筛选
 */
export default function FilterBar({ filters, onFilterChange }) {
  const [searchText, setSearchText] = useState(filters.searchText || "");

  const urgencyOptions = [
    { value: "高", label: "高" },
    { value: "中", label: "中" },
    { value: "低", label: "低" },
  ];

  const handleUrgencyToggle = (urgencyCode) => {
    const urgencyCodes = filters.urgencyCodes || [];
    const newUrgencyCodes = urgencyCodes.includes(urgencyCode)
      ? urgencyCodes.filter(u => u !== urgencyCode)
      : [...urgencyCodes, urgencyCode];
    onFilterChange({ ...filters, urgencyCodes: newUrgencyCodes });
  };

  const handleSearch = (e) => {
    e.preventDefault();
    onFilterChange({ ...filters, searchText });
  };

  return (
    <div className="bg-white rounded-lg border p-4 mb-4 space-y-3">
      {/* 搜索框 */}
      <form onSubmit={handleSearch} className="flex gap-2">
        <input
          type="text"
          placeholder="搜索申请号、标题、发起人..."
          value={searchText}
          onChange={(e) => setSearchText(e.target.value)}
          className="flex-1 px-3 py-2 border rounded text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
        />
        <button
          type="submit"
          className="px-4 py-2 bg-blue-500 text-white rounded text-sm hover:bg-blue-600 transition"
        >
          搜索
        </button>
      </form>

      {/* 紧急程度筛选 */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">紧急程度</label>
        <div className="flex flex-wrap gap-2">
          {urgencyOptions.map((opt) => (
            <button
              key={opt.value}
              onClick={() => handleUrgencyToggle(opt.value)}
              className={`px-3 py-1 rounded text-sm border transition ${
                (filters.urgencyCodes || []).includes(opt.value)
                  ? "bg-blue-500 text-white border-blue-500"
                  : "bg-white border-gray-300 text-gray-700 hover:border-blue-400"
              }`}
            >
              {opt.label}
            </button>
          ))}
        </div>
      </div>

      {/* 清空筛选 */}
      {((filters.statusCodes && filters.statusCodes.length > 0) ||
        (filters.urgencyCodes && filters.urgencyCodes.length > 0) || 
        filters.searchText) && (
        <button
          onClick={() => onFilterChange({ searchText: "", statusCodes: [], urgencyCodes: [] })}
          className="text-sm text-blue-500 hover:text-blue-700"
        >
          清空筛选
        </button>
      )}
    </div>
  );
}