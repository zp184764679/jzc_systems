import React from "react";

const STATUS_MAP = {
  approved: "已批准",
  submitted: "待审批",
  rejected: "已驳回",
  draft: "草稿",
};

const STATUS_COLORS = {
  approved: "bg-green-100 text-green-700",
  submitted: "bg-yellow-100 text-yellow-700",
  rejected: "bg-red-100 text-red-700",
  draft: "bg-gray-100 text-gray-700",
};

const URGENCY_MAP = {
  high: "高",
  medium: "中",
  low: "低",
};

const URGENCY_COLORS = {
  high: "bg-red-100 text-red-700",
  medium: "bg-yellow-100 text-yellow-700",
  low: "bg-blue-100 text-blue-700",
};

const formatTime = (v) => {
  if (!v) return "-";
  try {
    const d = new Date(v);
    if (isNaN(d.getTime())) return "-";
    return d.toLocaleString("zh-CN", {
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return "-";
  }
};

/**
 * RequestCard - 请求卡片视图（移动版）
 */
export default function RequestCard({
  loading,
  list,
  emptyMessage,
  onRowClick,
  onApprove,
  onReject,
  showTodoActions = false,
}) {
  if (loading) {
    return (
      <div className="p-6 text-center text-gray-500">加载中...</div>
    );
  }

  if (!list.length) {
    return (
      <div className="p-6 text-center text-gray-500">
        {emptyMessage || "暂无数据"}
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {list.map((item) => {
        const statusCode = item.status_code || "draft";
        const urgencyCode = item.urgency || "medium";

        return (
          <div key={item.id} className="bg-white border rounded-lg p-4 space-y-2">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="font-medium text-sm">{item.prNumber}</div>
                <div className="text-sm text-gray-600 mt-1">{item.title}</div>
              </div>
            </div>

            <div className="flex gap-2 flex-wrap text-xs">
              <span
                className={`px-2 py-0.5 rounded ${
                  URGENCY_COLORS[urgencyCode] || "bg-gray-100"
                }`}
              >
                {item.urgency || URGENCY_MAP[urgencyCode] || urgencyCode}
              </span>
              <span
                className={`px-2 py-0.5 rounded ${
                  STATUS_COLORS[statusCode] || "bg-gray-100"
                }`}
              >
                {item.status || STATUS_MAP[statusCode] || statusCode}
              </span>
            </div>

            <div className="text-xs text-gray-500">
              {item.owner_name} • {formatTime(item.created_at)}
            </div>

            <div className="flex gap-2 pt-2">
              <button
                onClick={() => onRowClick(item.id)}
                className="flex-1 px-2 py-1 text-xs border rounded hover:bg-gray-50 transition"
              >
                详情
              </button>
              {showTodoActions && statusCode === "submitted" && (
                <>
                  <button
                    onClick={() => onApprove(item.id)}
                    className="flex-1 px-2 py-1 text-xs bg-green-50 border border-green-200 text-green-700 rounded hover:bg-green-100 transition"
                  >
                    批准
                  </button>
                  <button
                    onClick={() => onReject(item.id)}
                    className="flex-1 px-2 py-1 text-xs bg-red-50 border border-red-200 text-red-700 rounded hover:bg-red-100 transition"
                  >
                    驳回
                  </button>
                </>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}